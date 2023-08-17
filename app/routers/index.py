from typing import Annotated

from fastapi import APIRouter, HTTPException, Response, status

from lib.models.patent import PatentDataToClient
from lib.database import reformat_mongodb_id_field, fetch_one_patent
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
async def post_patent(
    patent_spif: Annotated[str, PATENT_SPIF_PATH], api_response: Response
):
    # First, see if patent already exists in DB.
    db_response = await fetch_one_patent(patent_spif)
    if db_response:
        # TODO Create CustomKeywordIndex.
        patent_nodes = get_patent_nodes(db_response, service_context)
        custom_index = CustomKeywordTableIndex(
            patent_nodes,
            service_context=service_context,
            keyword_extract_template=extract_keyword_prompt,
            max_keywords_per_chunk=1,
        )
        # TODO Set description for later use by sqqe and save index to Mongo.
        api_response.status_code = status.HTTP_200_OK
        return reformat_mongodb_id_field(db_response)
    else:
        raise HTTPException(404, "Patent not found in MongoDB")
