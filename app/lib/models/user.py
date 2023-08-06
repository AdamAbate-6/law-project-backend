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
