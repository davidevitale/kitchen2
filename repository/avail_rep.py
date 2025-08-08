import etcd3
from typing import Optional
from model.kitchen_availability import KitchenAvailability

class AvailabilityRepository:
    def __init__(self, host="localhost", port=2379):
        self.etcd = etcd3.client(host=host, port=port)

    def save_availability(self, availability: KitchenAvailability):
        """Salva stato della cucina in etcd"""
        self.etcd.put(f"kitchen:{availability.kitchen_id}:availability", availability.json())

    def get_availability(self, kitchen_id: str) -> Optional[KitchenAvailability]:
        """Recupera stato della cucina"""
        value, _ = self.etcd.get(f"kitchen:{kitchen_id}:availability")
        return KitchenAvailability.parse_raw(value) if value else None

    def update_load(self, kitchen_id: str, load: int):
        """Aggiorna il carico di lavoro"""
        availability = self.get_availability(kitchen_id)
        if availability:
            availability.current_load = load
            self.save_availability(availability)

    def set_operational(self, kitchen_id: str, operational: bool):
        """Aggiorna stato operativo (aperta/chiusa)"""
        availability = self.get_availability(kitchen_id)
        if availability:
            availability.kitchen_operational = operational
            self.save_availability(availability)
