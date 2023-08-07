"""
Pydantic models for data communicated between frontend and backend related to
patents, specifically involving results retrieved using BigQuery or a cache of
such results in the "patents" collection of the database.
"""

from pydantic import BaseModel


class PatentDataToClient(BaseModel):
    """
    Patent data obtained from BigQuery or from MongoDB cache of earlier
    queries.
    """

    mongo_id: str
    spif: str
    title: str
    abstract: str
    claims: str
