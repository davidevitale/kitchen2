
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from uuid import UUID, uuid4

# 🔹 Modello per rappresentare un piatto
class Dish(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    price: float
    available_quantity: int

# 🔹 Modello per rappresentare una cucina
class Kitchen(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    location: Optional[str] = None


# 🔹 Modello per rappresentare il menu di una cucina
class Menu(BaseModel):
    kitchen_id: UUID
    items: Dict[UUID, Dish]  # chiave = dish_id, valore = oggetto Dish
