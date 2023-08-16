from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from lib.models.patent import PatentDataToClient
from lib.database import reformat_mongodb_id_field, fetch_one_patent
from lib.api_validators import PATENT_SPIF_PATH


router = APIRouter(
    prefix="/api/index",
    tags=["index"],
    responses={404: {"description": "Not found"}},
)


@router.post("/{patent_spif}", response_model=PatentDataToClient)
async def post_patent(
    patent_spif: Annotated[str, PATENT_SPIF_PATH], api_response: Response
):
    # First, see if patent already exists in DB.
    db_response = await fetch_one_patent(patent_spif)
    if db_response:
        # TODO Create CustomKeywordIndex.
        api_response.status_code = status.HTTP_200_OK
        return reformat_mongodb_id_field(db_response)
    else:
        raise HTTPException(404, "Patent not found in MongoDB")
