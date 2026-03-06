from typing import Optional, Literal
from pydantic import BaseModel, validator, Field


class ShareTextRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=102400)
    type: Literal["text"] = "text"

    @validator("text")
    def text_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v


class ShareResponse(BaseModel):
    code: str
    expires_in: int
    type: str
    message: str = "Share created successfully"


class RetrieveResponse(BaseModel):
    type: str
    content: Optional[str] = None
    filename: Optional[str] = None
    download_url: Optional[str] = None
    expires_in: int
    created_at: Optional[str] = None


class ErrorResponse(BaseModel):
    detail: str
