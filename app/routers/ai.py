from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from lib.models.ai import AiResponse
from lib.api_validators import PROJECT_ID_QUERY, USER_ID_QUERY
from lib.database import (
    fetch_one_project,
    fetch_one_patent,
    modify_project_chat,
)
from lib.llm import construct_ai_prompt, generate_ai_response

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
    print(project_entry["patents"][user_id])
    if len(project_entry["patents"][user_id]) > 0:
        patent_metadata = project_entry["patents"][user_id][0]
        patent_spif = patent_metadata["office"] + patent_metadata["number"]
        patent = await fetch_one_patent(patent_spif)
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
