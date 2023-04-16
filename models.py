from pydantic import BaseModel


class User(BaseModel):
    # _id will be populated if object of User class is being returned from MongoDB; if the object is being posted, _id should not exist as it will be generated automatically by MongoDB.
    _id: str | None = None
    first_name: str
    last_name: str
    email_address: str
    project_ids: list[str]


class ChatEntry(BaseModel):
    # Each Chat message must have a source, indicating "ai" or "user", and a msg, giving what that source said.
    source: str
    msg: str


class Project(BaseModel):
    # _id will be populated if object of Project class is being returned from MongoDB; if the object is being posted, _id should not exist as it will be generated automatically by MongoDB.
    _id: str | None = None
    name: str
    # chat is a dictionary with as many entries as users on the project. Each key is a user ID. Each value is a list of Chat messages between that user and the AI.
    chat: dict[str, list[ChatEntry]]
    user_ids: list[str]
    document_ids: list[str]


class UserInput(BaseModel):
    """
    This comes from the UI and so has to specify the user in addition to message contents.
    """
    user_id: str
    msg: str


class AiResponse(BaseModel):
    """
    This is the object FastAPI returns from a /api/ai GET.
    Eventually may add other fields containing links to referenced documents.
    """
    msg: str