from pydantic import BaseModel


class UserDataFromClient(BaseModel):
    """
    Input expected from client for POSTing a new user. mongo_id/_id is not specified as it will be generated automatically by MongoDB.
    """
    first_name: str
    last_name: str
    email_address: str
    project_ids: list[str]

class UserDataEditsFromClient(BaseModel):
    """
    Input expected from client for PUTting modifications to an existing user. mongo_id/_id is not specified because it is a path parameter in PUT.
    """
    first_name: str | None = None
    last_name: str | None = None
    email_address: str | None = None
    project_ids: list[str] | None = None
    

class UserDataToClient(BaseModel):
    """
    Return type expected from server after GETting a user or POSTing a new user. mongo_id is the string representation of the user entry's _id field.
    """
    # mongo_id will be populated if object of User class is being returned from MongoDB.
    mongo_id: str
    first_name: str
    last_name: str
    email_address: str
    project_ids: list[str]

# ==========================================================

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

# ==========================================================

class PatentDataToClient(BaseModel):
    mongo_id: str
    spif: str
    title: str
    abstract: str
    claims: str

# ==========================================================

# class UserInput(BaseModel):
#     """
#     This comes from the UI and so has to specify the user in addition to message contents or patent info.
#     """
#     user_id: str
#     msg: str | None = None
#     patent_number: str | None = None  # E.g. D631,198S
#     patent_office: str | None = None  # E.g. WO


class AiResponse(BaseModel):
    """
    This is the object FastAPI returns from a /api/ai GET.
    Eventually may add other fields containing links to referenced documents.
    """
    msg: str