# services/order_status_service.py
import uuid
from datetime import datetime, timezone
from typing import Optional
from model.order import Order
from model.status import OrderStatus, StatusEnum
from repository.order_status_repository import OrderStatusRepository

class OrderStatusService:
    """
    Servizio specializzato nella gestione CRUD dello stato degli ordini.
    """
    def __init__(self, status_repo: OrderStatusRepository):
        self._status_repo = status_repo

    async def create_initial_status(self, order: Order) -> Optional[OrderStatus]:
        """Crea il record di stato iniziale quando un ordine viene assegnato."""
        if not order.kitchen_id:
            return None
            
        status = OrderStatus(
            order_id=order.order_id,
            kitchen_id=order.kitchen_id,
            status=StatusEnum.RECEIVED
        )
        await self._status_repo.save(status)
        return status

    async def update_status(self, order_id: uuid.UUID, new_status: StatusEnum) -> bool:
        """Aggiorna lo stato di un ordine esistente."""
        status_record = await self._status_repo.get_by_id(order_id)
        if not status_record:
            return False
        
        status_record.status = new_status
        status_record.updated_at = datetime.now(timezone.utc)
        await self._status_repo.save(status_record)
        return True
