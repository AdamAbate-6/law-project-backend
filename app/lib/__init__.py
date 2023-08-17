import os
import pathlib

import yaml

# from llama_index import LLMPredictor, ServiceContext
# from llama_index.node_parser import SimpleNodeParser
# from langchain import OpenAI


config_dir = str(pathlib.Path(os.path.abspath(__file__)).parents[3])
config_path = os.path.join(config_dir, "config.yaml")
with open(config_path, "r") as f:
    config = yaml.safe_load(f)
os.environ["OPENAI_API_KEY"] = config["openai"]


# node_parser = SimpleNodeParser.from_defaults(
#     chunk_size=1028,
#     include_metadata=True,
#     include_prev_next_rel=True,
# )
# llm_predictor = LLMPredictor(
#     llm=OpenAI(
#         temperature=0,
#         model_name="gpt-3.5-turbo",
#         openai_api_key=os.environ["OPENAI_API_KEY"],
#     )
# )

# from llama_index.logger import LlamaLogger

# service_context = ServiceContext.from_defaults(
#     chunk_size=1028,
#     llm_predictor=llm_predictor,
#     node_parser=node_parser,
#     llama_logger=LlamaLogger(),
# )
