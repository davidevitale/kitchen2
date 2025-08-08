from repository.avail_rep import AvailabilityRepository
from model.kitchen_availability import KitchenAvailability

class KitchenService:
    def __init__(self, availability_repo: AvailabilityRepository):
        self.availability_repo = availability_repo

    def set_availability(self, availability: KitchenAvailability):
        """Imposta stato cucina"""
        self.availability_repo.save_availability(availability)

    def get_availability(self, kitchen_id: str) -> KitchenAvailability:
        """Recupera stato cucina"""
        return self.availability_repo.get_availability(kitchen_id)

    def can_accept_order(self, kitchen_id: str) -> bool:
        """
        Controlla se la cucina può accettare un ordine:
        - Deve essere operativa
        - current_load < max_capacity
        """
        availability = self.get_availability(kitchen_id)
        if not availability:
            return False
        return (
            availability.kitchen_operational
            and availability.current_load < availability.max_capacity
        )

    def decrease_capacity(self, kitchen_id: str):
        """Decrementa il numero di ordini in lavorazione"""
        availability = self.get_availability(kitchen_id)
        if availability and availability.current_load > 0:
            availability.current_load -= 1
            self.set_availability(availability)

    def increase_capacity(self, kitchen_id: str):
        """
        Incrementa il numero di ordini in lavorazione
        senza superare max_capacity
        """
        availability = self.get_availability(kitchen_id)
        if availability:
            if availability.current_load < availability.max_capacity:
                availability.current_load += 1
                self.set_availability(availability)
            else:
                print(f"[WARN] Capacità massima raggiunta per cucina {kitchen_id}")

