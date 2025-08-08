from repository.order_rep import OrderRepository
from service.menu_service import MenuService
from service.avail_service import KitchenService
from model.order import Order
from model.order_status import OrderStatus, StatusEnum

class OrderService:
    def __init__(self, order_repo: OrderRepository, menu_service: MenuService, kitchen_service: KitchenService):
        self.order_repo = order_repo
        self.menu_service = menu_service
        self.kitchen_service = kitchen_service

    def receive_order(self, order: Order) -> bool:
        """
        Riceve un ordine e controlla se la cucina può accettarlo.
        Se sì:
          - Salva ordine
          - Decrementa quantità piatti
          - Decrementa capacità cucina
          - Ritorna True per dire al producer Kafka di mandare ACCETTAZIONE
        """
        if not self.kitchen_service.can_accept_order(order.kitchen_id):
            return False

        # Controllo disponibilità di tutti i piatti
        menu = self.menu_service.get_menu(order.kitchen_id)
        if not menu:
            return False

        for item in order.items:
            dish = menu.items.get(item.dish_id)
            if not dish or dish.available_quantity < item.quantity:
                return False

        # Salvo ordine
        self.order_repo.save_order(order)

        # Decremento quantità piatti
        for item in order.items:
            self.menu_service.decrement_dish_quantity(order.kitchen_id, item.dish_id, item.quantity)

        # Decremento capacità cucina
        self.kitchen_service.decrease_capacity(order.kitchen_id)

        return True

    def update_order_status(self, order_id: str, kitchen_id: str, status: StatusEnum):
        """Aggiorna lo stato di un ordine"""
        order_status = OrderStatus(order_id=order_id, kitchen_id=kitchen_id, status=status)
        self.order_repo.save_order_status(order_status)

        # Se un ordine diventa PRONTO → capacità aumenta
        if status == StatusEnum.READY:
            self.kitchen_service.increase_capacity(kitchen_id)

    def get_order_status(self, order_id: str) -> OrderStatus:
        """Recupera stato ordine"""
        return self.order_repo.get_order_status(order_id)
