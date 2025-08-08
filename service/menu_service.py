import uuid
from repository.menu_repository import MenuRepository

class MenuService:
    """
    Contiene la logica di business per la gestione dell'inventario dei piatti.
    """
    def __init__(self, menu_repo: MenuRepository):
        self._menu_repo = menu_repo

    async def decrement_item_quantity(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID) -> bool:
        """
        Decrementa la quantità disponibile di un piatto.
        """
        item = await self._menu_repo.get_menu_item(kitchen_id, dish_id)
        if not item or item.available_quantity <= 0:
            # LOG: Piatto non trovato o quantità esaurita.
            return False
        
        item.available_quantity -= 1
        
        # Usiamo il metodo del repository che sovrascrive l'item.
        await self._menu_repo.create_menu_item(kitchen_id, item)
        return True

    async def increment_item_quantity(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID) -> bool:
        """
        Incrementa la quantità di un piatto (utile se un ordine viene annullato).
        """
        item = await self._menu_repo.get_menu_item(kitchen_id, dish_id)
        if not item:
            return False
            
        item.available_quantity += 1
        await self._menu_repo.create_menu_item(kitchen_id, item)
        return True