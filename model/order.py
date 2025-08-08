from pydantic import BaseModel, Field
from datetime import datetime, timezone

class Order(BaseModel):
    order_id: str 
    customer_id: str
    kitchen_id: str
    dish_id: str
    delivery_address: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
