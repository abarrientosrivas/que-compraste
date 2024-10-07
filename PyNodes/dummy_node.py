from PyLib.typed_messaging import PydanticMessageBroker, PydanticQueueConsumer
from pydantic import BaseModel
import os

class DummyMessage(BaseModel):
    text: str

class DummyNode:
    def __init__(self, consumer: PydanticQueueConsumer, broker: PydanticMessageBroker, input_queue: str):
        self.consumer = consumer
        self.broker = broker
        self.input_queue = input_queue
    
    def callback(self, message: DummyMessage):
        print(f"message received: {message.text}")
        with self.broker.get_publisher() as publisher:
            publisher.publish("", "", message)

    def start(self):
        self.consumer.start(self.input_queue, self.callback, DummyMessage)

    def stop(self):
        self.consumer.stop()

if __name__ == '__main__':
    broker = PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/')) # cambiar a dotenv

    node = DummyNode(broker.get_consumer(), broker, broker.ensure_queue(""))
    try:
        node.start()
    except KeyboardInterrupt:
        node.stop()