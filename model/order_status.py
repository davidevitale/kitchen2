from pydantic import BaseModel, Field
from enum import Enum
import uuid

class StatusEnum(str, Enum):
    RECEIVED = "ricevuto"
    ACCEPTED = "accettato"
    IN_PREPARATION = "in preparazione"
    READY = "pronto"
    DELIVERED = "consegnato"

class OrderStatus(BaseModel):
    status_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="ID univoco dello stato")
    order_id: str
    kitchen_id: str
    status: StatusEnum

    class Config:
        schema_extra = {
            "example": {
                "order_id": "123e4567-e89b-12d3-a456-426614174000",
                "kitchen_id": "456e4567-e89b-12d3-a456-426614174111",
                "status": "in preparazione"
            }
        }
