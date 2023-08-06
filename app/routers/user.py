from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.lib.models.user import (
    UserDataToClient,
    UserDataEditsFromClient,
    UserDataFromClient,
)
from app.lib.database import (
    reformat_mongodb_id_field,
    fetch_one_user,
    create_user,
    modify_user,
)
from app.lib.api_validators import USER_EMAIL_PATH, USER_ID_PATH


router = APIRouter(
    prefix="/user",
    tags=["user"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{email}", response_model=UserDataToClient)
async def get_user_by_email(email: Annotated[str, USER_EMAIL_PATH]):
    db_response = await fetch_one_user(email)
    if db_response:
        return reformat_mongodb_id_field(db_response)
    raise HTTPException(404, f"There is no user with email {email}")


@router.post("/", response_model=UserDataToClient, status_code=status.HTTP_201_CREATED)
async def post_user(user_entry: UserDataFromClient):
    db_response = await create_user(user_entry.dict())
    if db_response:
        return reformat_mongodb_id_field(db_response)
    raise HTTPException(400, "Something went wrong / bad request")


@router.put("/{user_id}", response_model=UserDataToClient)
async def put_user_modifications(
    user_id: Annotated[str, USER_ID_PATH], user_entry: UserDataEditsFromClient
):
    user_edits = {k: v for k, v in user_entry.dict().items() if v is not None}
    response = await modify_user(user_id, updated_user=user_edits)

    if response:
        return reformat_mongodb_id_field(response)

    raise HTTPException(400, f"Something went wrong modifying user {user_id}.")
