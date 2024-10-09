from PyLib import typed_messaging
from API import schemas
from PyNodes.product_finder_node import ProductCode
from datetime import datetime, UTC
from dotenv import load_dotenv
import os

load_dotenv()

broker = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
with broker.get_publisher() as publisher:
    try:
        while True:
            exchange = input("Exchange: ")
            routing_key = input("Routing key: ")

            exit_flag = True
            while exit_flag:
                typename = input("Type: ")
                if typename == "img":
                    payload = schemas.ReceiptImageLocation(
                        path=input("path: "),
                        url=input("url: ")
                    )
                elif typename == "pro":
                    payload = schemas.Product(
                        id=0,
                        title=input("title: "),
                        description=input("description: "),
                        read_category=input("category: "),
                        created_at=datetime.now(UTC)
                    )
                elif typename == "code":
                    payload = ProductCode(
                        code=input("code: ")
                    )
                elif typename == "ent":
                    payload = schemas.EntityBase(
                        name="",
                        identification=input("cuit: ")
                    )
                else:
                    exit_flag = False
                    break

                publisher.publish(exchange, routing_key, payload)
    except KeyboardInterrupt:
        print("\nExiting gracefully...")