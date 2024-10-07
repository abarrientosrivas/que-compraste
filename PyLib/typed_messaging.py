from pika.adapters.blocking_connection import BlockingChannel
from pika.exceptions import ChannelClosedByBroker, ConnectionClosed, ChannelClosed, AMQPError
from pika.spec import Basic, BasicProperties
from pika import BlockingConnection, PlainCredentials, ConnectionParameters
from urllib.parse import urlparse
from pydantic import BaseModel
from typing import Callable, Type, Any
import json
import time
import threading
import queue
import logging

def bind_queue(queue_name: str, exchange_name: str, routing_key: str | None, conn: BlockingConnection):
    channel = conn.channel()
    channel.queue_bind(queue_name, exchange_name, routing_key, None)
    channel.close()

def ensure_queue(queue_name: str, conn: BlockingConnection) -> str:
    channel = conn.channel()
    try:
        declared_queue = channel.queue_declare(queue_name, passive=True).method.queue
    except ChannelClosedByBroker:
        channel = conn.channel()
        declared_queue = channel.queue_declare(queue_name, auto_delete=True).method.queue
    channel.close()
    return declared_queue

def ensure_exchange(exchange_name: str, conn: BlockingConnection):
    if exchange_name == "":
        return
    channel = conn.channel()
    try:
        channel.exchange_declare(exchange_name, passive=True)
    except ChannelClosedByBroker:
        channel = conn.channel()
        channel.exchange_declare(exchange_name, exchange_type='fanout', auto_delete=True)
    channel.close()

def get_connection_by_string(conn_string:str) -> BlockingConnection:
    parsed = urlparse(conn_string)
    
    credentials = PlainCredentials(parsed.username, parsed.password)
    pika_parameters = ConnectionParameters(
        host=parsed.hostname,
        port=parsed.port,
        virtual_host=parsed.path if parsed.path else '/',
        credentials=credentials,
        heartbeat=600,
        blocked_connection_timeout=300
    )
    return BlockingConnection(pika_parameters)

class PydanticQueueConsumer:
    def __init__(self, channel: BlockingChannel):
        self.channel = channel
        self.message_queue = queue.Queue()

    def on_message(
            self,
            channel: BlockingChannel, 
            method_frame: Basic.Deliver, 
            header_frame: BasicProperties, 
            body: bytes):
        self.message_queue.put((channel, method_frame, body))

    def start(self, queue_name: str, callback: Callable[[BaseModel], Any], expected_type: Type[BaseModel], error_callback: Callable[[Exception], Any] | None = None):
        self.should_consume = True
        self.expected_type = expected_type
        self.callback = callback
        self.error_callback = error_callback

        self.worker_thread = threading.Thread(target=self.process_messages)
        self.worker_thread.start()

        self.channel.basic_consume(queue_name, self.on_message)
        self.channel.basic_qos(prefetch_count=1)

        while self.should_consume:
            self.channel.connection.process_data_events(time_limit=1)
            time.sleep(0.1)

    def process_messages(self):
        while self.should_consume:
            try:
                channel, method_frame, body = self.message_queue.get(timeout=1)
                self.process_message(channel, method_frame, body)
            except queue.Empty:
                continue

    def process_message(self, channel, method_frame, body):
        try:
            json_data = json.loads(body.decode())
            obj = self.expected_type(**json_data)
            self.callback(obj)
            self.channel.connection.add_callback_threadsafe(
                lambda: channel.basic_ack(method_frame.delivery_tag)
            )
        except Exception as e:
            if self.error_callback:
                self.error_callback(e)
            self.channel.connection.add_callback_threadsafe(
                lambda: channel.basic_nack(method_frame.delivery_tag, requeue=False)
            )

    def stop(self):
        self.should_consume = False
        self.worker_thread.join()
        self.channel.stop_consuming()

class PydanticExchangePublisher:
    def __init__(self, conn_string: str):
        self.conn_string = conn_string
        self.connection = None
        self.channel = None

    def __enter__(self):
        self._connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _connect(self):
        self.connection = get_connection_by_string(self.conn_string)
        self.channel = self.connection.channel()

    def publish(self, exchange_name: str, routing_key: str, payload: BaseModel):
        try:
            self.channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=payload.model_dump_json()
            )
        except (ConnectionClosed, ChannelClosed) as e:
            logging.warning(f"Connection or channel closed: {e}. Reconnecting...")
            self._reconnect()
            self.channel.basic_publish(
                exchange=exchange_name,
                routing_key=routing_key,
                body=payload.model_dump_json()
            )
        except AMQPError as e:
            logging.error(f"AMQP Error: {e}")
            raise

    def _reconnect(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()
        self._connect()

    def close(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()

class PydanticMessageBroker:
    def __init__(self, conn_string: str):
        self.conn = get_connection_by_string(conn_string)
        self.conn_string = conn_string

    def get_channel(self) -> BlockingChannel:
        return self.conn.channel()
    
    def ensure_queue(self, queue_name: str) -> str:
        return ensure_queue(queue_name, self.conn)
    
    def ensure_exchange(self, exchange_name: str):
        ensure_exchange(exchange_name, self.conn)
        
    def bind_queue(self, queue_name: str, exchange_name: str, routing_key: str | None):
        bind_queue(queue_name, exchange_name, routing_key, self.conn)
    
    def get_consumer(self) -> PydanticQueueConsumer:
        return PydanticQueueConsumer(channel = self.get_channel())
    
    def get_publisher(self) -> PydanticExchangePublisher:
        return PydanticExchangePublisher(conn_string=self.conn_string)