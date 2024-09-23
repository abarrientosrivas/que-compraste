from PyLib import typed_messaging
from API import schemas
from PyNodes.product_finder_node import ProductCode
from PyNodes.image_to_compra_node import ImageLocation
from PyNodes.entity_finder_node import EntityIdentification
from datetime import datetime, UTC
from pika.exceptions import ChannelClosedByBroker
from dotenv import load_dotenv
import os

load_dotenv()

broker = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
publisher = broker.get_publisher()

try:
    while True:
        try:
            exchange = input("Exchange: ")
            routing_key = input("Routing key: ")

            exit_flag = True
            while exit_flag:
                typename = input("Type: ")
                if typename == "img":
                    payload = ImageLocation(
                        path=input("path: ")
                    )
                elif typename == "pro":
                    payload = schemas.Product(
                        id=0,
                        name=input("name: "),
                        description=input("description: "),
                        read_category=input("category: "),
                        created_at=datetime.now(UTC)
                    )
                elif typename == "code":
                    payload = ProductCode(
                        code=input("code: ")
                    )
                elif typename == "ent":
                    payload = EntityIdentification(
                        identification=input("cuit: ")
                    )
                else:
                    exit_flag = False
                    break

                publisher.publish(exchange, routing_key, payload)
        except ChannelClosedByBroker:
            print("Reconnecting...\n")
            broker = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
            publisher = broker.get_publisher()
except KeyboardInterrupt:
    print("\nExiting gracefully...")