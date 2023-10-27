from llama_index import (
    ServiceContext,
    Document,
    Prompt,
    StorageContext,
    load_index_from_storage,
)
from llama_index.data_structs import Node
from llama_index.storage.docstore import MongoDocumentStore
from llama_index.storage.index_store import MongoIndexStore
from llama_index.indices.base import BaseIndex

from lib.database import db_uri


extract_keyword_prompt = Prompt(
    "Some text is provided below. Given the text, extract up to {max_keywords}"
    " keywords from the text. Select keywords from the following options: "
    "['description', 'abstract', 'claims']. Avoid stopwords."
    "---------------------\n"
    "{text}\n"
    "---------------------\n"
    "Provide keywords in the following comma-separated format: 'KEYWORDS: "
    "<keywords>'\n"
)


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
        # this_section_prepended_msg = \
        #  f'=== Patent ===\n{patent_dict["spif"]}\n=== {section_title} ===\n'
        for node in nodes:
            # Seems like we don't need this since extra_info of node is put into
            #  context.
            # node.text = this_section_prepended_msg + node.text
            all_nodes.append(node)

    return all_nodes


def load_index(patent_spif: str) -> BaseIndex:
    """Connect to the databases holding indices and patent nodes and construct
    from them an index.

    Args:
        patent_spif (dict): String representing patent office code and number

    Returns:
        BaseIndex: The loaded index
    """

    index_store = MongoIndexStore.from_uri(
        uri=db_uri, db_name="law_patent_indices", namespace=patent_spif
    )
    doc_store = MongoDocumentStore.from_uri(
        uri=db_uri, db_name="law_patent_nodes", namespace=patent_spif
    )
    storage_context = StorageContext.from_defaults(
        index_store=index_store, docstore=doc_store
    )
    index = load_index_from_storage(storage_context)
    return index
