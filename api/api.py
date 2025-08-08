import logging
from uuid import UUID

from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel

# Importa i nostri servizi e repository
from service.avail_service import KitchenService
from service.menu_service import MenuService
from service.order_Service import OrderService
from service.order_processing import OrderProcessingService
from repository.menu_repository import MenuRepository
from repository.order_status_repository import OrderStatusRepository
from repository.kitchen_availability_repository import KitchenAvailabilityRepository

from producers.kitchen_event_producer import KitchenEventProducer

from model.order_status import OrderStatus

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Costanti e Configurazioni ---

KITCHEN_ID = UUID("123e4567-e89b-12d3-a456-426614174000")

REDIS_CONFIG = {"host": "localhost", "port": 6379, "db": 0}
ETCD_HOST = "localhost"
ETCD_PORT = 2379

# --- Inizializzazione delle Dipendenze ---

menu_repo = MenuRepository(redis_config=REDIS_CONFIG)
order_status_repo = OrderStatusRepository(host=ETCD_HOST, port=ETCD_PORT)
kitchen_availability_repo = KitchenAvailabilityRepository()

kitchen_producer = KitchenEventProducer(kitchen_id=KITCHEN_ID)

kitchen_availability_service = KitchenAvailabilityService(
    kitchen_repo=kitchen_availability_repo,
    kitchen_id=KITCHEN_ID
)

menu_service = MenuService(
    menu_repo=menu_repo,
    kitchen_id=KITCHEN_ID
)

order_status_service = OrderStatusService(
    status_repo=order_status_repo,
    kitchen_id=KITCHEN_ID,
    producer=kitchen_producer
)

order_processing_service = OrderProcessingService(
    kitchen_id=KITCHEN_ID,
    availability_service=kitchen_availability_service,
    menu_service=menu_service,
    status_service=order_status_service,
    producer=kitchen_producer
)

# --- Definizione modelli risposta ---

class MessageResponse(BaseModel):
    message: str

class KitchenStatusUpdate(BaseModel):
    is_operational: bool

# --- Dependency Providers ---

def get_order_processing_service() -> OrderProcessingService:
    return order_processing_service

def get_kitchen_availability_service() -> KitchenAvailabilityService:
    return kitchen_availability_service

def get_order_status_service() -> OrderStatusService:
    return order_status_service

# --- FastAPI App ---

app = FastAPI(
    title="Kitchen Service API",
    description="API per gestire le operazioni di una Ghost Kitchen."
)

# --- Endpoints ---

@app.post("/orders/{order_id}/ready", response_model=MessageResponse, status_code=202)
async def mark_order_as_ready(
    order_id: UUID,
    service: OrderProcessingService = Depends(get_order_processing_service)
):
    """
    Endpoint per un operatore per marcare un ordine come 'pronto per il ritiro'.
    """
    try:
        # Se handle_order_ready non è async, togli l'await
        await service.handle_order_ready(order_id)
        return {"message": "Stato ordine aggiornato a 'ready'. Notifica inviata."}
    except Exception as e:
        logger.error(f"Errore in mark_order_as_ready: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Errore interno durante l'aggiornamento stato ordine")


@app.put("/kitchen/status", response_model=MessageResponse, status_code=200)
def set_kitchen_operational_status(
    status_update: KitchenStatusUpdate,
    service: KitchenAvailabilityService = Depends(get_kitchen_availability_service)
):
    """
    Endpoint per aprire o chiudere la cucina.
    """
    try:
        service.set_operational_status(status_update.is_operational)
        status_text = "operativa" if status_update.is_operational else "chiusa"
        return {"message": f"Stato della cucina impostato su: {status_text}"}
    except Exception as e:
        logger.error(f"Errore in set_kitchen_operational_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Errore interno durante l'aggiornamento stato cucina")


@app.get("/orders/{order_id}/status", response_model=OrderStatus)
def get_order_status(
    order_id: UUID,
    service: OrderStatusService = Depends(get_order_status_service)
):
    """
    Endpoint per interrogare lo stato attuale di un ordine.
    """
    try:
        status = service.get_order_status(order_id)
        if not status:
            raise HTTPException(status_code=404, detail="Stato ordine non trovato")
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore in get_order_status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Errore interno durante il recupero stato ordine")
