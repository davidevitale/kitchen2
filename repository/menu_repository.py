import uuid
from typing import Dict, Optional
from model.menu import MenuItem, Menu

class MenuRepository:
    def __init__(self):
        # CORREZIONE: Struttura dati migliorata.
        # Mappa un kitchen_id a un dizionario di piatti (dish_id -> MenuItem).
        # Questo rende molto più efficiente recuperare un intero menù.
        self._menus: Dict[uuid.UUID, Dict[uuid.UUID, MenuItem]] = {}

    def create_menu_item(self, kitchen_id: uuid.UUID, menu_item: MenuItem) -> None:
        """Crea o aggiorna un piatto nel menu di una specifica cucina."""
        # Se la cucina non ha ancora un menù, lo crea.
        if kitchen_id not in self._menus:
            self._menus[kitchen_id] = {}
        self._menus[kitchen_id][menu_item.dish_id] = menu_item

    def get_menu_item(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID) -> Optional[MenuItem]:
        """Recupera un piatto specifico da una cucina."""
        kitchen_menu = self._menus.get(kitchen_id)
        if kitchen_menu:
            return kitchen_menu.get(dish_id)
        return None

    def delete_menu_item(self, kitchen_id: uuid.UUID, dish_id: uuid.UUID) -> bool:
        """Elimina un piatto dal menu."""
        if kitchen_id in self._menus and dish_id in self._menus[kitchen_id]:
            del self._menus[kitchen_id][dish_id]
            return True
        return False
    
    def get_menu(self, kitchen_id: uuid.UUID) -> Optional[Menu]:
        """
        CORREZIONE: Logica implementata correttamente.
        Costruisce e restituisce l'oggetto Menu completo per una cucina.
        """
        kitchen_menu_items = self._menus.get(kitchen_id)
        if kitchen_menu_items is not None:
            # Crea l'oggetto Menu al volo con la lista dei piatti.
            return Menu(
                kitchen_id=kitchen_id,
                items=list(kitchen_menu_items.values())
            )
        return None