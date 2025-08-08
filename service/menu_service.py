from typing import Optional
from uuid import UUID
from model.menu_item import Menu, Dish
from repository.menu_rep import MenuRepository

class MenuService:
    def __init__(self, menu_repo: MenuRepository):
        self.menu_repo = menu_repo

    def create_menu(self, menu: Menu):
        """Crea un nuovo menu"""
        self.menu_repo.save_menu(menu)

    def get_menu(self, kitchen_id: UUID) -> Optional[Menu]:
        """Recupera menu di una cucina"""
        return self.menu_repo.get_menu(kitchen_id)

    def update_menu(self, menu: Menu):
        """Aggiorna menu esistente"""
        self.menu_repo.save_menu(menu)

    def delete_menu(self, kitchen_id: UUID):
        """Elimina un menu"""
        self.menu_repo.delete_menu(kitchen_id)

    def update_dish_quantity(self, kitchen_id: UUID, dish_id: UUID, quantity: int):
        """Aggiorna quantità disponibile di un piatto"""
        self.menu_repo.update_dish_quantity(kitchen_id, dish_id, quantity)

    def decrement_dish_quantity(self, kitchen_id: UUID, dish_id: UUID, quantity: int):
        """Decrementa quantità dopo un ordine"""
        self.menu_repo.decrement_dish_quantity(kitchen_id, dish_id, quantity)
