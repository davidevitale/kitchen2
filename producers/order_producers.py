import asyncio
import json
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaConnectionError
from model import OrderStatus

# Nomi dei topic
AVAILABILITY_RESPONSE_TOPIC = "kitchen_availability_responses"
STATUS_UPDATE_TOPIC = "order_status_updates"

class EventProducer:
    def __init__(self, host='localhost', port=9092):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=f"{host}:{port}",
            value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8')
        )
        self._started = False

    async def start(self):
        # Logica di retry per la connessione
        if self._started: return
        for i in range(10):
            try:
                await self.producer.start()
                self._started = True
                print("✅ PRODUCER: Connesso a Kafka.")
                return
            except KafkaConnectionError:
                print(f"⚠️ PRODUCER: Connessione a Kafka fallita (tentativo {i+1})...")
                await asyncio.sleep(3)
        print("❌ ERRORE CRITICO (Producer): Impossibile connettersi a Kafka.")

    async def stop(self):
        if self._started:
            await self.producer.stop()
            print("🛑 PRODUCER: Disconnesso da Kafka.")

    async def publish_availability(self, order_id: int, kitchen_id: int, is_available: bool):
        """Pubblica la risposta di disponibilità della cucina."""
        message = {"order_id": order_id, "kitchen_id": kitchen_id, "available": is_available}
        await self.producer.send_and_wait(AVAILABILITY_RESPONSE_TOPIC, value=message)
        print(f"📬 PRODUCER: Risposta disponibilità per ordine {order_id} inviata.")

    async def publish_status_update(self, status: OrderStatus):
        """Pubblica un aggiornamento di stato dell'ordine."""
        await self.producer.send_and_wait(STATUS_UPDATE_TOPIC, value=status.dict())
        print(f"📬 PRODUCER: Aggiornamento stato per ordine {status.order_id} inviato.")