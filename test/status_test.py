import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock

# Importa tutti i modelli e servizi necessari
from model.order import Order
from model.status import StatusEnum
from repository.order_status_repository import OrderStatusRepository
from service.status_service import OrderStatusService

# ======================================================================
# --- Test per il OrderStatusService ---
# ======================================================================

@pytest.mark.asyncio
async def test_status_service_create_initial_status():
    """
    TEST: Verifica la corretta creazione dello stato iniziale di un ordine.
    """
    order = Order(
        order_id=uuid.uuid4(),
        customer_id=uuid.uuid4(),
        dish_id=uuid.uuid4(),
        delivery_address="Via Test 123",
        # Aggiungiamo il kitchen_id che nel tuo modello non c'è ma nel service sì
        kitchen_id=uuid.uuid4() 
    )

    mock_repo = MagicMock(spec=OrderStatusRepository)
    mock_repo.save = AsyncMock()

    status_service = OrderStatusService(status_repo=mock_repo)
    await status_service.create_initial_status(order)

    mock_repo.save.assert_called_once()
    saved_status = mock_repo.save.call_args[0][0]
    assert saved_status.order_id == order.order_id
    assert saved_status.kitchen_id == order.kitchen_id
    assert saved_status.status == StatusEnum.RECEIVED
