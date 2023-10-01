from typing import Annotated

from fastapi import APIRouter, HTTPException, Response, status
from llama_index import StorageContext
from llama_index.storage.index_store import MongoIndexStore
from llama_index.storage.docstore import MongoDocumentStore

from lib.models.patent import PatentDataToClient
from lib.database import reformat_mongodb_id_field, fetch_one_patent, db_uri
from lib.api_validators import PATENT_SPIF_PATH
from lib.index_utils import get_patent_nodes, extract_keyword_prompt
from lib.llm import service_context
from lib.custom_keyword_index import CustomKeywordTableIndex

router = APIRouter(
    prefix="/api/index",
    tags=["index"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{patent_spif}", response_model=PatentDataToClient)
async def post_patent_index(
    patent_spif: Annotated[str, PATENT_SPIF_PATH], api_response: Response
):
    # First, see if patent already exists in DB.
    db_response = await fetch_one_patent(patent_spif)
    if db_response:
        patent_dict = {k: v for k, v in db_response.items() if k != "_id"}
        patent_nodes = get_patent_nodes(patent_dict, service_context)

        # Index will be persisted to a DB named law_patent_indices in a
        #  collection whose name is the patent_spif.
        index_store = MongoIndexStore.from_uri(
            uri=db_uri, db_name="law_patent_indices", namespace=patent_spif
        )
        # Likewise, have to persist docs. Otherwise, querying a loaded index
        #  as a query engine will raise an error that a doc_id is not found.
        doc_store = MongoDocumentStore.from_uri(
            uri=db_uri, db_name="law_patent_nodes", namespace=patent_spif
        )
        doc_store.add_documents(patent_nodes)

        # NOTE: Specifying storage_context as a MongoIndexStore should
        #  automatically persist the index to MongoDB.
        custom_index = CustomKeywordTableIndex(
            patent_nodes,
            service_context=service_context,
            keyword_extract_template=extract_keyword_prompt,
            max_keywords_per_chunk=1,
            docstore=doc_store,
            storage_context=StorageContext.from_defaults(
                index_store=index_store, docstore=doc_store
            ),
        )
        # NOTE: Commenting out the below because it's unnecessary DB I/O bits.
        #  Can just construct the summary out of patent_spif when the sqqe is
        #  created.
        # custom_index.summary = (
        #     f"Use this index for queries about patent with SPIF {patent_spif}"
        # )
        # custom_index.storage_context.persist()
        api_response.status_code = status.HTTP_200_OK
        return reformat_mongodb_id_field(db_response)
    else:
        raise HTTPException(404, "Patent not found in MongoDB")
