from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from llama_index.tools import QueryEngineTool, ToolMetadata
from llama_index.query_engine import SubQuestionQueryEngine

from lib.models.ai import AiResponse
from lib.api_validators import PROJECT_ID_QUERY, USER_ID_QUERY
from lib.database import fetch_one_project, modify_project_chat
from lib.llm import construct_ai_prompt, generate_ai_response, service_context
from lib.index_utils import load_index

router = APIRouter(
    prefix="/api/ai",
    tags=["ai"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=AiResponse)
async def get_ai_response(
    project_id: Annotated[str, PROJECT_ID_QUERY],
    user_id: Annotated[str, USER_ID_QUERY],
    last_user_chat_msg: str,
):
    # Get the chat (list of dicts with 'source' and 'msg' keys) for this project and user.
    project_entry = await fetch_one_project(project_id)
    chat = project_entry["chat"]
    user_chat = chat[user_id]
    # Handle case that frontend's request to put last user msg in DB has not completed yet. In that case,
    #  append message from frontend to local copy of the un-updated chat log pulled from the DB.
    last_msg_in_db = user_chat[-1]
    db_is_up_to_date = (
        last_msg_in_db["source"] == "user"
        and last_msg_in_db["msg"] == last_user_chat_msg
    )
    if not db_is_up_to_date:
        user_chat.append({"source": "user", "msg": last_user_chat_msg})

    # Get the patent (TODO design prompt to allow more than one patent and then fetch all patents whose metadata is in project_entry['patents'][user_id]).
    if len(project_entry["patents"][user_id]) > 0:
        query_engine_tools = []
        for patent_metadata in project_entry["patents"][user_id]:
            patent_spif = patent_metadata["office"] + patent_metadata["number"]
            index = load_index(patent_spif)

            qe = QueryEngineTool(
                query_engine=index.as_query_engine(),
                metadata=ToolMetadata(
                    name=patent_spif,
                    description=f"Patent with SPIF {patent_spif}",
                ),
            )
            query_engine_tools.append(qe)

        query_engine = SubQuestionQueryEngine.from_defaults(
            query_engine_tools=query_engine_tools,
            service_context=service_context,
            use_async=False,
        )
        # 10/26/2023: The below fails on the following error:
        """Traceback (most recent call last):
        File "<string>", line 1, in <module>
        File "C:\Users\abate\.virtualenvs\law-project-backend-Kz-JhaCG\Lib\site-packages\llama_index\indices\query\base.py", line 23, in query
            response = self._query(str_or_query_bundle)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        File "C:\Users\abate\.virtualenvs\law-project-backend-Kz-JhaCG\Lib\site-packages\llama_index\query_engine\sub_question_query_engine.py", line 152, in _query
            response = self._response_synthesizer.synthesize(
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        File "C:\Users\abate\.virtualenvs\law-project-backend-Kz-JhaCG\Lib\site-packages\llama_index\response_synthesizers\base.py", line 122, in synthesize
            with self._callback_manager.event(
        File "C:\Python311\Lib\contextlib.py", line 137, in __enter__
            return next(self.gen)
                ^^^^^^^^^^^^^^
        File "C:\Users\abate\.virtualenvs\law-project-backend-Kz-JhaCG\Lib\site-packages\llama_index\callbacks\base.py", line 169, in event
            event.on_start(payload=payload)
        File "C:\Users\abate\.virtualenvs\law-project-backend-Kz-JhaCG\Lib\site-packages\llama_index\callbacks\base.py", line 242, in on_start
            self._callback_manager.on_event_start(
        File "C:\Users\abate\.virtualenvs\law-project-backend-Kz-JhaCG\Lib\site-packages\llama_index\callbacks\base.py", line 105, in on_event_start
            parent_id = global_stack_trace.get()[-1]
                        ~~~~~~~~~~~~~~~~~~~~~~~~^^^^
        IndexError: list index out of range
        """
        query_engine.query(last_user_chat_msg)

    else:
        patent = "No patent is available"

    prompt = construct_ai_prompt(user_chat, patent)
    ai_msg = generate_ai_response(prompt)

    # Put the AI-generated message in the user_chat list, and then make that updated list
    #  the entry for this user in the project. Update the DB accordingly.
    # Yes, I know, this is a GET endpoint, but I am ok updating the DB in it because in
    #  PUT and POST typically imply the client is sending data to the backend. Here the
    #  backend (i.e. the AI) is the one generating the data.
    new_chat_msg = {"source": "ai", "msg": ai_msg}
    user_chat.append(new_chat_msg)
    chat[user_id] = user_chat
    response = await modify_project_chat(project_id, updated_chat=chat)
    if not response:
        raise HTTPException(400, "Something went wrong.")

    data = AiResponse.parse_obj({"msg": ai_msg})
    return data
