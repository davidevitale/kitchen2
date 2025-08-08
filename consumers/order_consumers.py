import asyncio
import json
from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError
from model import OrderRequest
from service.avail_service import KitchenService

# Nomi dei topic da cui ascoltare
TOPICS = ["kitchen_availability_requests", "order_assignments", "order_status_requests"]

class EventConsumer:
    def __init__(self, service: KitchenService, host='localhost', port=9092):
        self.service = service
        self.consumer = AIOKafkaConsumer(
            *TOPICS,
            bootstrap_servers=f"{host}:{port}",
            value_deserializer=lambda v: json.loads(v.decode('utf-8')),
            group_id="kitchen_service_group",
            auto_offset_reset="latest"
        )
        self._started = False

    async def start(self):
        # Logica di retry
        if self._started: return
        for i in range(10):
            try:
                await self.consumer.start()
                self._started = True
                print("✅ CONSUMER: Connesso a Kafka.")
                return
            except KafkaConnectionError:
                print(f"⚠️ CONSUMER: Connessione a Kafka fallita (tentativo {i+1})...")
                await asyncio.sleep(3)
        print("❌ ERRORE CRITICO (Consumer): Impossibile connettersi a Kafka.")

    async def stop(self):
        if self._started:
            await self.consumer.stop()
            print("🛑 CONSUMER: Disconnesso da Kafka.")

    async def listen(self):
        """Loop principale di ascolto."""
        if not self._started: return
        print(f"🎧 CONSUMER: In ascolto su topics: {', '.join(TOPICS)}")
        async for msg in self.consumer:
            print(f"📬 CONSUMER: Messaggio ricevuto su topic '{msg.topic}': {msg.value}")
            try:
                if msg.topic == "kitchen_availability_requests":
                    request = OrderRequest(**msg.value)
                    await self.service.check_availability(request)
                
                elif msg.topic == "order_assignments":
                    order_id = msg.value['order_id']
                    assigned_kitchen_id = msg.value['kitchen_id']
                    await self.service.handle_order_assignment(order_id, assigned_kitchen_id)

                elif msg.topic == "order_status_requests":
                    order_id = msg.value['order_id']
                    await self.service.get_and_publish_order_status(order_id)
            except Exception as e:
                print(f"🔥 ERRORE durante l'elaborazione del messaggio: {e}")