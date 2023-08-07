"""
Pydantic models for data...
1) Stored in the "projects" collection of MongoDB and therefore communicated
between backend and database, and
2) Communicated between the backend and frontend for project updates for one
or more users
"""

from pydantic import BaseModel


class ChatEntry(BaseModel):
    """
    This is text and associated metadata for a single chat message, as stored
    in a document of the "projects" collection in MongoDB.
    Each Chat message must have a source, indicating "ai" or "user", and a
    msg, giving what that source said.
    """

    source: str
    msg: str


class PatentEntry(BaseModel):
    """
    This is information about a patent stored in a document of the "projects"
    collection in MongoDB. It is sufficient for finding the actual patent in
    the "patents" collection.
    A patent entry consists of a country code and a
    """

    office: str  # E.g. WO
    number: str  # E.g. D631,198S


class ProjectDataFromClient(BaseModel):
    """
    Input expected from client for POSTing a new project. mongo_id/_id is not
    specified as it will be generated automatically by MongoDB.
    """

    name: str
    # chat is a dictionary with as many entries as users on the project. Each
    #  key is a user ID. Each value is a list of Chat messages between that
    #  user and the AI.
    chat: dict[str, list[ChatEntry]]
    patents: dict[str, list[PatentEntry]]
    user_ids: list[str]
    document_ids: list[str]


class ProjectDataEditsFromClient(BaseModel):
    """
    Input expected from client for PUTting edits to a project. Unlike
    ProjectDataFromClient, all fields are optional; only specified fields
    result in project edits.
    """

    name: str | None = None
    # chat is a dictionary with as many entries as users on the project. Each
    #  key is a user ID. Each value is a list of Chat messages between that
    #  user and the AI.
    chat: dict[str, list[ChatEntry]] | None = None
    patents: dict[str, list[PatentEntry]] | None = None
    user_ids: list[str] | None = None
    document_ids: list[str] | None = None


class ProjectDataToClient(BaseModel):
    """
    Return type expected from server after GETting a user or POSTing a new
    project. mongo_id is the string representation of the user entry's _id
    field.
    """

    mongo_id: str
    name: str
    # chat is a dictionary with as many entries as users on the project. Each
    #  key is a user ID. Each value is a list of Chat messages between that
    #  user and the AI.
    chat: dict[str, list[ChatEntry]]
    patents: dict[str, list[PatentEntry]]
    user_ids: list[str]
    document_ids: list[str]
