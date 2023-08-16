import re
from typing import Sequence

from llama_index.indices.keyword_table.base import KeywordTableIndex
from llama_index.data_structs.data_structs import KeywordTable
from llama_index.data_structs import Node
from llama_index.schema import MetadataMode


class CustomKeywordTableIndex(KeywordTableIndex):
    def _add_nodes_to_index(
        self,
        index_struct: KeywordTable,
        nodes: Sequence[Node],
        show_progress: bool = False,
    ) -> None:
        for n in nodes:
            keywords = re.search(
                r"(?<=section: )\w+(?=\s)",
                n.get_content(metadata_mode=MetadataMode.ALL),
            )
            assert keywords is not None, (
                f"Could not find section title in node {n} with following "
                f"content: {n.get_content(metadata_mode=MetadataMode.ALL)}"
            )
            keywords = keywords.group()
            if keywords == "claims":
                keywords = ["claim", "claims"]
            elif keywords == "description":
                keywords = ["description", "descriptions"]
            elif keywords == "abstract":
                keywords = ["abstract", "abstracts"]
            index_struct.add_node(list(keywords), n)
