
import uuid
from model.status import StatusEnum
from model.order import Order
from repository.order_repository import OrderRepository
from .kitchen_service import KitchenService
from .menu_service import MenuService
from status_service import OrderStatusService

class OrderService:
    """
    Servizio principale che orchestra gli altri servizi per gestire il ciclo di vita di un ordine.
    È il cervello di questo microservizio.
    """
    def __init__(self, 
                 order_repo: OrderRepository,
                 kitchen_service: KitchenService, 
                 menu_service: MenuService, 
                 status_service: OrderStatusService):
        self._order_repo = order_repo
        self._kitchen_service = kitchen_service
        self._menu_service = menu_service
        self._status_service = status_service

    async def handle_newly_assigned_order(self, order: Order) -> bool:
        """
        Questa è la funzione principale chiamata quando il microservizio riceve un nuovo ordine
        già assegnato a una cucina.
        """
        if not order.kitchen_id:
            # LOG: Ricevuto ordine senza un kitchen_id, impossibile processarlo.
            return False
            
        # 1. Decrementa la quantità del piatto dal menù/inventario.
        quantity_updated = await self._menu_service.decrement_item_quantity(order.kitchen_id, order.dish_id)
        if not quantity_updated:
            # LOG: Fallito l'aggiornamento della quantità, forse il piatto è esaurito.
            # Qui si potrebbe comunicare al servizio chiamante che l'ordine è stato rifiutato.
            return False

        # 2. Incrementa il carico di lavoro della cucina.
        load_updated = await self._kitchen_service.increment_load(order.kitchen_id)
        if not load_updated:
            # LOG: Fallito l'incremento del carico, forse la cucina è piena.
            # **AZIONE CORRETTIVA**: Dobbiamo ripristinare la quantità del piatto!
            await self._menu_service.increment_item_quantity(order.kitchen_id, order.dish_id)
            return False

        # 3. Se tutto va bene, salva l'ordine e crea il suo stato iniziale.
        await self._order_repo.save(order)
        await self._status_service.create_initial_status(order)
        
        return True

    async def handle_order_status_update(self, order_id: uuid.UUID, kitchen_id: uuid.UUID, new_status: StatusEnum) -> bool:
        """
        Gestisce le conseguenze di un cambio di stato.
        """
        status_updated = await self._status_service.update_status(order_id, new_status)
        if not status_updated:
            return False

        # Logica di business: se l'ordine è pronto, decrementa il carico della cucina.
        if new_status == StatusEnum.READY_FOR_PICKUP:
            await self._kitchen_service.decrement_load(kitchen_id)
        
        # Logica di business: se l'ordine viene annullato, ripristina le risorse.
        elif new_status == StatusEnum.CANCELLED:
            order = await self._order_repo.get_by_id(order_id)
            if order:
                await self._kitchen_service.decrement_load(order.kitchen_id)
                await self._menu_service.increment_item_quantity(order.kitchen_id, order.dish_id)

        return True