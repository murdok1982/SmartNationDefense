from pydantic import BaseModel, Field


class ContributorIntakeRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None


class ContributorIntakeResponse(BaseModel):
    response: str
    session_id: str
