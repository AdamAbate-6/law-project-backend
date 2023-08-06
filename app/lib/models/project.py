from pydantic import BaseModel


class ChatEntry(BaseModel):
    # Each Chat message must have a source, indicating "ai" or "user", and a msg, giving what that source said.
    source: str
    msg: str


class PatentEntry(BaseModel):
    office: str  # E.g. WO
    number: str  # E.g. D631,198S


class ProjectDataFromClient(BaseModel):
    """
    Input expected from client for POSTing a new project. mongo_id/_id is not specified as it will be generated automatically by MongoDB.
    """

    name: str
    # chat is a dictionary with as many entries as users on the project. Each key is a user ID. Each value is a list of Chat messages between that user and the AI.
    chat: dict[str, list[ChatEntry]]
    patents: dict[str, list[PatentEntry]]
    user_ids: list[str]
    document_ids: list[str]


class ProjectDataEditsFromClient(BaseModel):
    name: str | None = None
    # chat is a dictionary with as many entries as users on the project. Each key is a user ID. Each value is a list of Chat messages between that user and the AI.
    chat: dict[str, list[ChatEntry]] | None = None
    patents: dict[str, list[PatentEntry]] | None = None
    user_ids: list[str] | None = None
    document_ids: list[str] | None = None


class ProjectDataToClient(BaseModel):
    """
    Return type expected from server after GETting a user or POSTing a new project. mongo_id is the string representation of the user entry's _id field.
    """

    mongo_id: str
    name: str
    # chat is a dictionary with as many entries as users on the project. Each key is a user ID. Each value is a list of Chat messages between that user and the AI.
    chat: dict[str, list[ChatEntry]]
    patents: dict[str, list[PatentEntry]]
    user_ids: list[str]
    document_ids: list[str]
