from pydantic import BaseModel

class KitchenAvailability(BaseModel):
    kitchen_id: str
    kitchen_operational: bool               # Cucina attiva?
    current_load: int                       # Ordini in lavorazione
    max_capacity: int = 10  # valore di default, modificabile