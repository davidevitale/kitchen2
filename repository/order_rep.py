import json
import redis
from typing import Optional
from model.order import Order
from model.order_status import OrderStatus

class OrderRepository:
    def __init__(self, host="localhost", port=6379):
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)

    def save_order(self, order: Order):
        self.redis.set(f"order:{order.order_id}", order.json())

    def get_order(self, order_id: str) -> Optional[Order]:
        data = self.redis.get(f"order:{order_id}")
        return Order.parse_raw(data) if data else None

    def save_order_status(self, status: OrderStatus):
        self.redis.set(f"order_status:{status.order_id}", status.json())

    def get_order_status(self, order_id: str) -> Optional[OrderStatus]:
        data = self.redis.get(f"order_status:{order_id}")
        return OrderStatus.parse_raw(data) if data else None
