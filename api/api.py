# ======================================================================
# --- File: api/main.py (CORRETTO + PATCH dish update) ---
# ======================================================================
import os
import uuid
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from redis.cluster import ClusterNode

# Importa modelli, servizi e repository
from model.menu import MenuItem
from model.status import OrderStatus, StatusEnum
from model.kitchen import KitchenAvailability
from model.order import Order
from model.messaging_models import OrderRequest

from service.kitchen_service import KitchenService
from service.menu_service import MenuService
from service.order_service import OrderOrchestrationService
from service.status_service import OrderStatusService

from repository.kitchen_repository import KitchenAvailabilityRepository
from repository.menu_repository import MenuRepository
from repository.order_status_repository import OrderStatusRepository
from repository.order_repository import OrderRepository

from producers.producers import EventProducer

# ======================================================================
# --- Blocco di Inizializzazione e Dependency Injection ---
# ======================================================================

KAFKA_BROKERS = "localhost:9092"
ETCD_HOST = "localhost"
ETCD_PORT = 2379

try:
    KITCHEN_ID = uuid.UUID(os.environ.get("KITCHEN_ID"))
    print(f"✅ ID Cucina caricato dall'ambiente: {KITCHEN_ID}")
except (ValueError, TypeError):
    KITCHEN_ID = uuid.uuid4()
    print(f"⚠️ ATTENZIONE: KITCHEN_ID non trovato. Generato un ID casuale: {KITCHEN_ID}")

# Repositories
kitchen_repo = KitchenAvailabilityRepository(host=ETCD_HOST, port=ETCD_PORT)
redis_cluster_nodes = [
    ClusterNode("redis-node-1", 6379),
    ClusterNode("redis-node-2", 6379),
    ClusterNode("redis-node-3", 6379)
]
menu_repo = MenuRepository(redis_cluster_nodes=redis_cluster_nodes)
order_status_repo = OrderStatusRepository(host=ETCD_HOST, port=ETCD_PORT)
order_repo = OrderRepository(host=ETCD_HOST, port=ETCD_PORT)

# Producer Kafka
event_producer = EventProducer(bootstrap_servers=KAFKA_BROKERS)

# Services
kitchen_service = KitchenService(kitchen_repo=kitchen_repo)
menu_service = MenuService(menu_repo=menu_repo)
status_service = OrderStatusService(status_repo=order_status_repo)
orchestration_service = OrderOrchestrationService(
    order_repo=order_repo,
    kitchen_service=kitchen_service,
    menu_service=menu_service,
    status_service=status_service,
    event_producer=event_producer
)

# Provider FastAPI
def get_kitchen_service(): return kitchen_service
def get_menu_service(): return menu_service
def get_orchestrator(): return orchestration_service
def get_status_service(): return status_service

# ======================================================================
# --- FastAPI App & Endpoints ---
# ======================================================================

app = FastAPI(
    title="Kitchen Service API",
    description="API per gestire le operazioni di una Ghost Kitchen."
)

# Modelli request
class QuantityUpdateRequest(BaseModel):
    available_quantity: int

class StatusUpdateRequest(BaseModel):
    status: StatusEnum

class MenuItemUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    available_quantity: Optional[int] = None

# --- Kitchen Endpoints ---
@app.get("/kitchen", response_model=KitchenAvailability)
async def get_kitchen_status(kitchen_service: KitchenService = Depends(get_kitchen_service)):
    kitchen_state = await kitchen_service.get_by_id(KITCHEN_ID)
    if not kitchen_state:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stato cucina non trovato.")
    return kitchen_state

@app.patch("/kitchen")
async def update_kitchen_status(
    is_operational: bool,
    kitchen_service: KitchenService = Depends(get_kitchen_service)
):
    success = await kitchen_service.set_operational_status(KITCHEN_ID, is_operational)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Impossibile aggiornare lo stato della cucina.")
    return {"message": "Stato cucina aggiornato con successo."}

# --- Menu Endpoints ---
@app.get("/menu/dishes", response_model=List[MenuItem])
async def get_all_dishes(menu_service: MenuService = Depends(get_menu_service)):
    menu = await menu_service.get_menu(KITCHEN_ID)
    return menu.items if menu and menu.items else []

@app.get("/menu/dishes/{dish_id}", response_model=MenuItem)
async def get_dish_detail(dish_id: uuid.UUID, menu_service: MenuService = Depends(get_menu_service)):
    item = await menu_service.get_menu_item(KITCHEN_ID, dish_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato.")
    return item

@app.post("/menu/dishes", status_code=status.HTTP_201_CREATED, response_model=MenuItem)
async def create_menu_item(dish: MenuItem, menu_service: MenuService = Depends(get_menu_service)):
    success = await menu_service.create_menu_item(KITCHEN_ID, dish)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Creazione piatto fallita.")
    return dish

@app.patch("/menu/dishes/{dish_id}/quantity", response_model=MenuItem)
async def update_dish_quantity(
    dish_id: uuid.UUID,
    request: QuantityUpdateRequest,
    menu_service: MenuService = Depends(get_menu_service)
):
    item = await menu_service.get_menu_item(KITCHEN_ID, dish_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato.")
    item.available_quantity = request.available_quantity
    await menu_service.update_menu_item(KITCHEN_ID, item)
    return item

@app.patch("/menu/dishes/{dish_id}", response_model=MenuItem)
async def update_menu_item(
    dish_id: uuid.UUID,
    request: MenuItemUpdateRequest,
    menu_service: MenuService = Depends(get_menu_service)
):
    """Aggiorna più campi di un piatto: nome, descrizione, prezzo, quantità."""
    item = await menu_service.get_menu_item(KITCHEN_ID, dish_id)
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato.")

    if request.name is not None:
        item.name = request.name
    if request.description is not None:
        item.description = request.description
    if request.price is not None:
        item.price = request.price
    if request.available_quantity is not None:
        item.available_quantity = request.available_quantity

    await menu_service.update_menu_item(KITCHEN_ID, item)
    return item

@app.delete("/menu/dishes/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(dish_id: uuid.UUID, menu_service: MenuService = Depends(get_menu_service)):
    success = await menu_service.delete_menu_item(KITCHEN_ID, dish_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Piatto non trovato o impossibile eliminare.")
    return {"message": "Piatto eliminato con successo."}

# --- Orders Endpoints ---
@app.get("/orders", response_model=List[OrderStatus])
async def get_active_orders(status_service: OrderStatusService = Depends(get_status_service)):
    return await status_service.get_all_active_orders_by_kitchen(KITCHEN_ID)

@app.get("/orders/{order_id}", response_model=Order)
async def get_order_detail(order_id: uuid.UUID, orchestrator: OrderOrchestrationService = Depends(get_orchestrator)):
    order = await orchestrator.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordine non trovato.")
    return order

@app.post("/user/orders", status_code=201, response_model=Order)
async def create_user_order(order_request: OrderRequest, orchestrator: OrderOrchestrationService = Depends(get_orchestrator)):
    """
    Endpoint per il cliente finale per fare un ordine.
    Internamente chiama `check_availability_and_propose` e gestisce il flusso.
    """
    # L’orchestrator gestisce tutto il flusso (proposta -> assegnazione -> salvataggio)
    saved_order = await orchestrator.create_order_from_user(order_request)
    if not saved_order:
        raise HTTPException(status_code=500, detail="Ordine non creato.")
    return saved_order

@app.post("/orders", status_code=status.HTTP_201_CREATED, response_model=Order)
async def create_order(order: Order, orchestrator: OrderOrchestrationService = Depends(get_orchestrator)):
    success = await orchestrator.handle_newly_assigned_order(order)
    if not success:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Creazione ordine fallita.")
    saved_order = await orchestrator.get_order_by_id(order.order_id)
    if not saved_order:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ordine creato ma non recuperabile.")
    return saved_order

@app.post("/orders/proposals", status_code=status.HTTP_202_ACCEPTED)
async def propose_order(request: OrderRequest, orchestrator: OrderOrchestrationService = Depends(get_orchestrator)):
    await orchestrator.check_availability_and_propose(request)
    return {"message": "Richiesta di candidatura inviata alle cucine."}

@app.patch("/orders/{order_id}/status", status_code=status.HTTP_202_ACCEPTED)
async def update_order_status(
    order_id: uuid.UUID,
    request: StatusUpdateRequest,
    orchestrator: OrderOrchestrationService = Depends(get_orchestrator)
):
    success = await orchestrator.handle_order_status_update(order_id, request.status)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordine non trovato o aggiornamento fallito.")
    return {"message": "Richiesta di aggiornamento stato accettata."}
