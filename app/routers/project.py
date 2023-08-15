from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Query, Response, status

from lib.models.project import (
    ProjectDataToClient,
    ProjectDataFromClient,
    ProjectDataEditsFromClient,
)
from lib.api_validators import PROJECT_ID_PATH, USER_ID_QUERY
from lib.database import (
    reformat_mongodb_id_field,
    fetch_one_project,
    modify_project,
    create_project,
)

router = APIRouter(
    prefix="/api/project",
    tags=["project"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{project_id}", response_model=ProjectDataToClient)
async def get_project_by_id(project_id: Annotated[str, PROJECT_ID_PATH]):
    db_response = await fetch_one_project(project_id)
    if db_response:
        return reformat_mongodb_id_field(db_response)
    raise HTTPException(404, f"There is no project with ID {project_id}")


@router.post(
    "/",
    response_model=ProjectDataToClient,
    status_code=status.HTTP_201_CREATED,
)
async def post_project(project_entry: ProjectDataFromClient):
    db_response = await create_project(project_entry.dict())
    if db_response:
        return reformat_mongodb_id_field(db_response)
    raise HTTPException(400, "Something went wrong / bad request")


@router.put("/{project_id}", response_model=ProjectDataToClient)
async def put_project_modifications(
    project_id: Annotated[str, PROJECT_ID_PATH],
    project_edits: ProjectDataEditsFromClient,
    user_id: Annotated[str | None, USER_ID_QUERY] = None,
):
    """Modify project document in DB corresponding to project_id. If user_id is
    specified (not None), only apply project_edits to the specified user.
    Otherwise, each field in project_edits will completely replace its
    corresponding field in the project document.

    Args:
        project_id (str): Mongo DB project document's _id
        project_edits (ProjectDataEditsFromClient): Object whose fields add to
            or replace data in the project document
        user_id (str | None, optional): If specified, only data for this user
            is replaced by project_edits. Defaults to None.

    Raises:
        HTTPException: If the DB request to modify the project fails.

    Returns:
        ProjectDataToClient: The project document with _id stringified.
    """

    project_edits_dict = {
        k: v for k, v in project_edits.dict().items() if v is not None
    }

    def only_edit_field_for_user(
        field_name: str,
        user_id: str,
        existing_project_entry: dict,
        project_edits: dict,
    ) -> dict:
        """Return a modified version of project_edits that has all original
        info from existing_project_entry for field_name with only the entry
        under user_id kept in the state specified by project_edits.

        Rationale is that modify_project takes project_edits and uses its keys
        to replace the *entire* corresponding keys' values in the DB.
        So make sure parts of the field corresponding to non-user_id
        users remain unchanged by putting them in their original state (i.e.
        from existing_project_entry) in project_edits.

        Args:
            field_name (str): Key of DB document to edit (see models.py's
                ProjectDataEditsFromClient for keys)
            user_id (str): Mongo DB user document's _id for user whose value
                of field_name we want to edit.
            existing_project_entry (dict): Dict representation of Mongo DB
                document for project
                E.g. {'chat': {*user_name*: *chat_entry*}, 'patents':
                {*user_name*: *patent_entry*}}
            project_edits (dict): Dict having key-value pairs for just the
                fields of the project edited in this request.

        Returns:
            dict: Version of project_edits containing the new info in
                project_edits and unedited info for other users on this
                project.
        """

        tmp = dict()
        if user_id in existing_project_entry[field_name].keys():
            # If user is in project, modify their value of field_name (e.g.
            #  'chat') to have the corresponding value in project_edits.
            tmp = {
                uid: project_edits[field_name][user_id]
                if uid == user_id
                else existing_field_value
                for uid, existing_field_value in existing_project_entry[
                    field_name
                ].items()
            }
        else:
            # If the user is not in the project, create a new place for them
            #  under field_name.
            tmp = existing_project_entry[field_name]
            tmp[user_id] = project_edits[field_name][user_id]

        project_edits[field_name] = tmp
        return project_edits

    # Only add patents to the project that don't already exist for user. Also,
    #  only modify the part of patents corresponding to queried user. Or if
    #  user is not in project, add user entry to patents.
    existing_project_entry = None
    if "patents" in project_edits_dict.keys() and user_id is not None:
        existing_project_entry = await fetch_one_project(project_id)
        patents = existing_project_entry["patents"]
        user_patents = patents[user_id]

        patents_to_add = []
        for p in project_edits_dict["patents"][user_id]:
            edit_patent = {"office": p["office"], "number": p["number"]}

            # Check if patent already exists in user's list of patents.
            patent_exists = any([p == edit_patent for p in user_patents])
            if not patent_exists:
                patents_to_add.append(edit_patent)

        project_edits_dict["patents"][user_id] = patents_to_add

        project_edits_dict = only_edit_field_for_user(
            "patents", user_id, existing_project_entry, project_edits_dict
        )

    # Only modify the part of the chat corresponding to queried user. Or if
    #  user is not in project, add user entry to chat.
    if "chat" in project_edits_dict.keys() and user_id is not None:
        if existing_project_entry is None:
            existing_project_entry = await fetch_one_project(project_id)

        project_edits_dict = only_edit_field_for_user(
            "chat", user_id, existing_project_entry, project_edits_dict
        )

    response = await modify_project(
        project_id, updated_project=project_edits_dict
    )

    if response:
        return reformat_mongodb_id_field(response)
