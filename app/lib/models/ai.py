"""
Pydantic models for data communicated between the backend and frontend
relating to AI processing.
"""

from pydantic import BaseModel


class AiResponse(BaseModel):
    """
    This is the object FastAPI returns from a /api/ai GET.
    Eventually may add other fields containing links to referenced documents.
    """

    msg: str
