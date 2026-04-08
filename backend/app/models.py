from typing import Dict, List, Optional

from pydantic import BaseModel, Field, model_validator


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str


class AIConnectivityCheckResponse(BaseModel):
    model: str
    reply: str


class ColumnSnapshot(BaseModel):
    id: str
    slotKey: str
    title: str
    position: int
    version: int
    cardIds: List[str]


class CardSnapshot(BaseModel):
    id: str
    columnId: str
    title: str
    details: str
    sortOrder: float
    version: int


class BoardSnapshot(BaseModel):
    version: int
    columns: List[ColumnSnapshot]
    cards: Dict[str, CardSnapshot]


class BoardResponse(BaseModel):
    board: BoardSnapshot


class CardResponse(BaseModel):
    card: CardSnapshot


class ColumnRenameRequest(BaseModel):
    title: str = Field(min_length=1)
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_title(self) -> "ColumnRenameRequest":
        self.title = self.title.strip()
        if not self.title:
            raise ValueError("Column title cannot be empty.")
        return self


class CardCreateRequest(BaseModel):
    columnId: str
    title: str = Field(min_length=1)
    details: str = ""
    beforeCardId: Optional[str] = None
    afterCardId: Optional[str] = None

    @model_validator(mode="after")
    def validate_request(self) -> "CardCreateRequest":
        self.title = self.title.strip()
        self.details = self.details.strip()
        if not self.title:
            raise ValueError("Card title cannot be empty.")
        if self.beforeCardId and self.afterCardId:
            raise ValueError("Provide either beforeCardId or afterCardId, not both.")
        return self


class CardUpdateRequest(BaseModel):
    title: str = Field(min_length=1)
    details: str
    version: int = Field(ge=1)

    @model_validator(mode="after")
    def validate_request(self) -> "CardUpdateRequest":
        self.title = self.title.strip()
        self.details = self.details.strip()
        if not self.title:
            raise ValueError("Card title cannot be empty.")
        return self


class CardMoveRequest(BaseModel):
    targetColumnId: str
    version: int = Field(ge=1)
    beforeCardId: Optional[str] = None
    afterCardId: Optional[str] = None

    @model_validator(mode="after")
    def validate_request(self) -> "CardMoveRequest":
        if self.beforeCardId and self.afterCardId:
            raise ValueError("Provide either beforeCardId or afterCardId, not both.")
        return self
