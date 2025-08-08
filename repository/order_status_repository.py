import uuid
from typing import Dict, Optional
from model.status import OrderStatus, StatusEnum

class OrderStatusRepository:
    def __init__(self):
        self._statuses: Dict[uuid.UUID, OrderStatus] = {}

    def save(self, order_status: OrderStatus) -> None:
        """Crea o aggiorna lo stato di un ordine."""
        self._statuses[order_status.order_id] = order_status
    
    def update_status(self, order_id: uuid.UUID, new_status: StatusEnum) -> bool:
        """Aggiorna solo il campo 'status' di un record esistente."""
        if order_id in self._statuses:
            self._statuses[order_id].status = new_status
            return True
        return False

    def get_by_id(self, order_id: uuid.UUID) -> Optional[OrderStatus]:
        """Recupera lo stato di un ordine."""
        return self._statuses.get(order_id)