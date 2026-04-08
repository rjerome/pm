from typing import Annotated, Dict, List, Optional, Union
from typing import Literal

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


class AIConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_content(self) -> "AIConversationMessage":
        self.content = self.content.strip()
        if not self.content:
            raise ValueError("Conversation message content cannot be empty.")
        return self


class AIChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: List[AIConversationMessage] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_message(self) -> "AIChatRequest":
        self.message = self.message.strip()
        if not self.message:
            raise ValueError("Message cannot be empty.")
        return self


class AIRenameColumnOperation(BaseModel):
    type: Literal["rename_column"]
    columnId: str
    title: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_title(self) -> "AIRenameColumnOperation":
        self.title = self.title.strip()
        if not self.title:
            raise ValueError("Column title cannot be empty.")
        return self


class AICreateCardOperation(BaseModel):
    type: Literal["create_card"]
    columnId: str
    title: str = Field(min_length=1)
    details: str = ""
    beforeCardId: Optional[str] = None
    afterCardId: Optional[str] = None

    @model_validator(mode="after")
    def validate_request(self) -> "AICreateCardOperation":
        self.title = self.title.strip()
        self.details = self.details.strip()
        if not self.title:
            raise ValueError("Card title cannot be empty.")
        if self.beforeCardId and self.afterCardId:
            raise ValueError("Provide either beforeCardId or afterCardId, not both.")
        return self


class AIUpdateCardOperation(BaseModel):
    type: Literal["update_card"]
    cardId: str
    title: str = Field(min_length=1)
    details: str

    @model_validator(mode="after")
    def validate_request(self) -> "AIUpdateCardOperation":
        self.title = self.title.strip()
        self.details = self.details.strip()
        if not self.title:
            raise ValueError("Card title cannot be empty.")
        return self


class AIMoveCardOperation(BaseModel):
    type: Literal["move_card"]
    cardId: str
    targetColumnId: str
    beforeCardId: Optional[str] = None
    afterCardId: Optional[str] = None

    @model_validator(mode="after")
    def validate_request(self) -> "AIMoveCardOperation":
        if self.beforeCardId and self.afterCardId:
            raise ValueError("Provide either beforeCardId or afterCardId, not both.")
        return self


class AIDeleteCardOperation(BaseModel):
    type: Literal["delete_card"]
    cardId: str


AIBoardOperation = Annotated[
    Union[
        AIRenameColumnOperation,
        AICreateCardOperation,
        AIUpdateCardOperation,
        AIMoveCardOperation,
        AIDeleteCardOperation,
    ],
    Field(discriminator="type"),
]


class AIAssistantPayload(BaseModel):
    reply: str = Field(min_length=1)
    operations: List[AIBoardOperation] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_reply(self) -> "AIAssistantPayload":
        self.reply = self.reply.strip()
        if not self.reply:
            raise ValueError("Assistant reply cannot be empty.")
        return self


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


class AIChatResponse(BaseModel):
    model: str
    reply: str
    operations: List[AIBoardOperation]
    boardUpdated: bool
    board: BoardSnapshot


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
