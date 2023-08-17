import logging
import sys
import json
import os
import pathlib
import re
import yaml
from google.cloud import bigquery
from langchain import OpenAI
from llama_index.node_parser import SimpleNodeParser
from llama_index.data_structs import Node
from llama_index.schema import MetadataMode
from llama_index import (
    LLMPredictor,
    Document,
    Prompt,
    SimpleDirectoryReader,
    ServiceContext,
    StorageContext,
    ComposableGraph,
    GPTVectorStoreIndex,
    GPTKeywordTableIndex,
    GPTTreeIndex,
    GPTListIndex,
    download_loader,
)

root_dir = "C:\\Users\\adam\\Code\\law_project"

with open(os.path.join(root_dir, "config.yaml"), "r") as f:
    config = yaml.safe_load(f)

os.environ["OPENAI_API_KEY"] = config["openai"]
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
    root_dir, "law-project-service-account.json"
)

logging.basicConfig(filename="log.log", level=logging.DEBUG, force=True)
logging.getLogger().addHandler(logging.StreamHandler(stream=sys.stdout))

# client = bigquery.Client(project='law-project')
# Tried above with user account. Trying below with service account.
# client = bigquery.Client()


# NOTE: Below method is replaced by main.py's post_patent() and big_query_utils.py's query_patent()
def get_patent_dict(patent_spif):
    cache_path = pathlib.Path(
        os.path.join(
            root_dir,
            f"law-project-backend\\notebooks\\data\\patents\\{patent_spif}.json",
        )
    )
    if not cache_path.exists():
        print(f"Could not find cached {cache_path}. Querying BigQuery.")

        # NOTE: New-lines here are purely visual, so need space at end of each line.
        #  E.g. otherwise end of SELECT line into FROM becomes `as descriptionFROM`.
        QUERY = (
            f"SELECT spif_publication_number as spif, t.text as title,  a.text as abstract, c.text as claims, d.text as description "
            f"FROM `patents-public-data.patents.publications`, UNNEST(title_localized) as t, UNNEST(abstract_localized) as a,  UNNEST(claims_localized) as c, UNNEST(description_localized) as d "
            f'WHERE spif_publication_number = "{patent_spif}" '
            f"LIMIT 100"
        )
        query_job = None  # client.query(QUERY)  # Send API request.
        rows = query_job.result()  # Waits for query to finish.

        # `rows` is an iterator, but SPIF should be unique to one patent, so we should only iterate once.
        num_iters = 0
        patent_data = dict()
        for row in rows:
            patent_data["spif"] = row.spif
            patent_data["title"] = row.title
            patent_data["abstract"] = row.abstract
            patent_data["claims"] = row.claims
            # TODO Add in description

            num_iters += 1
            assert (
                num_iters == 1
            ), f"More than one entry was returned from BigQuery query to patent SPIF {patent_spif}; that cannot be correct."

        found_patent_in_bq = True if len(patent_data) > 1 else False

        if not cache_path.parent.exists():
            cache_path.parent.mkdir(parents=True)

        with open(str(cache_path), "w") as f:
            json.dump(patent_data, f)

    else:
        with open(str(cache_path), "r") as f:
            patent_data = json.load(f)

    return patent_data


# NOTE: Similar code will go in main.py's get_ai_response()
patent_spifs = ["US8205344B2", "US9889572B2"]
patent_texts = []
patent_dicts = []
for spif in patent_spifs:
    patent_data = get_patent_dict(spif)
    patent_texts.append(json.dumps(patent_data))
    patent_dicts.append(patent_data)


# NOTE: This is called by make_patent_indices(). Should probably live in
#  llm_utils.py
def get_patent_nodes(
    patent_dict: dict, service_context: ServiceContext
) -> list[Node]:
    all_nodes = []
    for section_title, section_content in patent_dict.items():
        if section_title == "spif" or section_title == "title":
            # No need to include SPIF and title as separate nodes for the low
            #  level index to choose from. Because they are being put in
            #  `extra_info`, if the node_parser has `include_extra_info` set
            #  to True, then spif and title will appear at the top of every
            #  node.
            continue

        doc = Document(
            text=section_content,
            extra_info={
                "spif": patent_dict["spif"],
                "title": patent_dict["title"],
                "section": section_title,
            },
        )

        nodes = service_context.node_parser.get_nodes_from_documents([doc])
        # this_section_prepended_msg = f'=== Patent ===\n{patent_dict["spif"]}\n=== {section_title} ===\n'
        for node in nodes:
            # Seems like we don't need this since extra_info of node is put into
            #  context.
            # node.text =  + node.text
            all_nodes.append(node)

    return all_nodes


# Subtract the max length of the message prepended to each node from the desired
#  chunk size so that, in get_patent_nodes(), msg can be prepended to each node
#  without violating desired chunk size. NOTE: Did not end up being necessary since context gets prepended during node.get_text()
# max_node_prepended_msg_length = 50
node_parser = SimpleNodeParser.from_defaults(
    chunk_size=1028,
    include_metadata=True,
    include_prev_next_rel=True,
)
llm_predictor = LLMPredictor(
    llm=OpenAI(
        temperature=0,
        model_name="gpt-3.5-turbo",
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )
)

from llama_index.logger import LlamaLogger

service_context = ServiceContext.from_defaults(
    chunk_size=1028,
    llm_predictor=llm_predictor,
    node_parser=node_parser,
    llama_logger=LlamaLogger(),
)


# NOTE: This will go in llm_utils.py
import re
from llama_index.indices.keyword_table.base import KeywordTableIndex
from llama_index.data_structs.data_structs import KeywordTable
from typing import Sequence


class CustomKeywordTableIndex(KeywordTableIndex):
    def _add_nodes_to_index(
        self,
        index_struct: KeywordTable,
        nodes: Sequence[Node],
        show_progress: bool = False,
    ) -> None:
        for n in nodes:
            keywords = re.search(
                "(?<=section: )\w+(?=\s)",
                n.get_content(metadata_mode=MetadataMode.ALL),
            ).group()
            if keywords == "claims":
                keywords = ["claim", "claims"]
            elif keywords == "description":
                keywords = ["description", "descriptions"]
            elif keywords == "abstract":
                keywords = ["abstract", "abstracts"]
            index_struct.add_node(list(keywords), n)


# NOTE: This will be called by get_ai_response() after checking whether the indices already exist in a collection named for the user and the patent SPIF.
# TODO Need to implement that checking part.
# TODO Need to implement index saving to DB.
def make_patent_indices(
    patent_dicts: list[dict], service_context: ServiceContext
):
    extract_keyword_prompt = Prompt(
        "Some text is provided below. Given the text, extract up to {max_keywords} "
        "keywords from the text. Select keywords from the following options: "
        "['description', 'abstract', 'claims']. Avoid stopwords."
        "---------------------\n"
        "{text}\n"
        "---------------------\n"
        "Provide keywords in the following comma-separated format: 'KEYWORDS: <keywords>'\n"
    )

    patent_keyword_indices = []
    index_summaries = []
    patent_spifs = []
    os.environ[
        "OPENAI_API_KEY"
    ] = "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"
    for patent_dict in patent_dicts:
        nodes = get_patent_nodes(patent_dict, service_context)
        index_summaries.append(
            f'Use this index for queries about patent {patent_dict["spif"]}'
        )
        patent_spifs.append(patent_dict["spif"])
        patent_keyword_indices.append(
            CustomKeywordTableIndex(
                nodes,
                service_context=service_context,
                keyword_extract_template=extract_keyword_prompt,
                max_keywords_per_chunk=1,
            )
        )
    return patent_keyword_indices, patent_spifs, index_summaries


patent_keyword_indices, patent_spifs, index_summaries = make_patent_indices(
    patent_dicts, service_context
)


# NOTE: This will be part of get_ai_response() no matter what because query engine must be constructed at eval time.
from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index.query_engine import SubQuestionQueryEngine

# setup base query engine as tool
query_engine_tools = [
    QueryEngineTool(
        query_engine=index.as_query_engine(),
        metadata=ToolMetadata(
            name=spif, description=f"Patent with SPIF {spif}"
        ),
    )
    for index, spif in zip(patent_keyword_indices, patent_spifs)
]

# See https://github.com/jerryjliu/llama_index/issues/7090; need to set
#  use_async to False until resolved.
query_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=query_engine_tools,
    service_context=service_context,
    use_async=False,
)

response = query_engine.query(
    "Compare and constrast claim 1 of patent US8205344B2 with claim 1 of US9889572B2"
)
