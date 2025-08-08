# producers/order_producer.py
from aiokafka import AIOKafkaProducer
import asyncio
import json

class OrderProducer:
    def __init__(self, kafka_bootstrap_servers: str):
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        self.producer = None

    async def start(self):
        self.producer = AIOKafkaProducer(bootstrap_servers=self.kafka_bootstrap_servers)
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send_order_created(self, order: dict):
        topic = "order.created"
        await self.producer.send_and_wait(topic, json.dumps(order).encode("utf-8"))

    async def send_order_status_updated(self, status_update: dict):
        topic = "order.status.updated"
        await self.producer.send_and_wait(topic, json.dumps(status_update).encode("utf-8"))

    async def send_kitchen_availability_updated(self, availability: dict):
        topic = "kitchen.availability.updated"
        await self.producer.send_and_wait(topic, json.dumps(availability).encode("utf-8"))
