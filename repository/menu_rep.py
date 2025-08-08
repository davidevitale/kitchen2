import json
from typing import Optional
from redis.cluster import RedisCluster
from model.menu_item import Menu, Dish
from uuid import UUID

class MenuRepository:
    def __init__(self, redis_nodes: list):
        """
        redis_nodes = [{"host": "localhost", "port": 7000}, ...]
        """
        self.redis = RedisCluster(startup_nodes=redis_nodes, decode_responses=True)

    def save_menu(self, menu: Menu):
        """Salva o aggiorna un menu in Redis Cluster"""
        self.redis.set(f"menu:{menu.kitchen_id}", menu.json())

    def get_menu(self, kitchen_id: UUID) -> Optional[Menu]:
        """Recupera il menu di una cucina"""
        data = self.redis.get(f"menu:{kitchen_id}")
        return Menu.parse_raw(data) if data else None

    def delete_menu(self, kitchen_id: UUID):
        """Elimina un menu"""
        self.redis.delete(f"menu:{kitchen_id}")

    def update_dish_quantity(self, kitchen_id: UUID, dish_id: UUID, quantity: int):
        """Aggiorna la quantità disponibile di un piatto"""
        menu = self.get_menu(kitchen_id)
        if menu and dish_id in menu.items:
            menu.items[dish_id].available_quantity = quantity
            self.save_menu(menu)

    def decrement_dish_quantity(self, kitchen_id: UUID, dish_id: UUID, quantity: int):
        """Decrementa la quantità di un piatto dopo un ordine"""
        menu = self.get_menu(kitchen_id)
        if menu and dish_id in menu.items:
            menu.items[dish_id].available_quantity -= quantity
            self.save_menu(menu)
