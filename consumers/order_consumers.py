# consumers/order_consumer.py
from aiokafka import AIOKafkaConsumer
import asyncio
import json
from model.kitchen_availability import KitchenAvailability

class OrderConsumer:
    def __init__(self, kafka_bootstrap_servers: str, menu_service, kitchen_service):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.consumer = None
        self.menu_service = menu_service
        self.kitchen_service = kitchen_service

    async def start(self):
        self.consumer = AIOKafkaConsumer(
            "order.created", "order.status.updated", "kitchen.availability.updated",
            bootstrap_servers=self.kafka_bootstrap_servers,
            group_id="order_service_group"
        )
        await self.consumer.start()
        try:
            async for msg in self.consumer:
                event = json.loads(msg.value.decode("utf-8"))
                topic = msg.topic
                await self.handle_event(topic, event)
        finally:
            await self.consumer.stop()

    async def handle_event(self, topic: str, event: dict):
        if topic == "order.created":
            # logica per nuovo ordine
            print(f"Ricevuto ordine: {event}")
            # es. check disponibilità cucina
            can_accept = self.kitchen_service.can_accept_order(event['kitchen_id'])
            if can_accept:
                self.kitchen_service.increase_capacity(event['kitchen_id'])
                print(f"Ordine accettato per cucina {event['kitchen_id']}")
            else:
                print(f"Cucina non disponibile per ordine {event['order_id']}")

        elif topic == "order.status.updated":
            # logica aggiornamento stato ordine
            print(f"Aggiornamento stato ordine: {event}")
            old_status = event.get("old_status")
            new_status = event.get("new_status")
            kitchen_id = event.get("kitchen_id")
            if old_status != "pronto" and new_status == "pronto":
                self.kitchen_service.decrease_capacity(kitchen_id)
            elif old_status != "in preparazione" and new_status == "in preparazione":
                self.kitchen_service.increase_capacity(kitchen_id)

        elif topic == "kitchen.availability.updated":
            # logica aggiornamento disponibilità cucina
            print(f"Aggiornamento disponibilità cucina: {event}")
            availability = KitchenAvailability(**event)
            self.kitchen_service.set_availability(availability)
