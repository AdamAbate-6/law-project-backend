from pydantic import BaseModel


class PatentDataToClient(BaseModel):
    mongo_id: str
    spif: str
    title: str
    abstract: str
    claims: str
