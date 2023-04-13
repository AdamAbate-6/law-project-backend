from pydantic import BaseModel


class User(BaseModel):
    first_name: str
    last_name: str
    email_address: str
    project_ids: list[str]


class Chat(BaseModel):
    # Each Chat message must have a source, indicating "ai" or "user", and a msg, giving what that source said.
    source: str
    msg: str


class Project(BaseModel):
    name: str
    # chat is a dictionary with as many entries as users on the project. Each key is a user ID. Each value is a list of Chat messages between that user and the AI.
    chat: dict[str, list[Chat]]
    user_ids: list[str]
    document_ids: list[str]