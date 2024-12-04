import argparse
import logging
import threading
import os
import sys
from API.schemas import Purchase, PredictionCreate, PredictionItemCreate
from DemandForecast.xgboost_predictor import predict_next_purchase_dates, predict_next_purchase_quantities
from PyLib import typed_messaging, request_tools
from pydantic import ValidationError
from json.decoder import JSONDecodeError
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

PREDICT_DAYS_AHEAD = int(os.getenv("PREDICT_DAYS_AHEAD","90"))

class PurchasePredictorNode:
    def __init__(self, restockables_endpoint: str, historics_endpoint: str, predictions_endpoint: str, consumer: typed_messaging.PydanticQueueConsumer, input_queue: str):
        self.consumer = consumer
        self.restockables_endpoint = restockables_endpoint
        self.historics_endpoint = historics_endpoint
        self.predictions_endpoint = predictions_endpoint
        self.input_queue = input_queue
        self.stop_event = threading.Event()

    def callback(self, message: Purchase):
        if not message.items:
            logging.info(f"Ignoring purchase with no items")
            return
        
        response = request_tools.send_request_with_retries("get", f"{self.restockables_endpoint}product-codes", stop_event=self.stop_event)
        if response is None:
            raise Exception(f"Cannot retrieve restockables. There was no response from server")
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve restockables. Status code: {response.status_code}. Server response: {response.text}")
        restockable_product_codes: list = response.json()
        
        response = request_tools.send_request_with_retries("get", f"{self.restockables_endpoint}categories", stop_event=self.stop_event)
        if response is None:
            raise Exception(f"Cannot retrieve restockables. There was no response from server")
        if response.status_code != 200:
            raise Exception(f"Failed to retrieve restockables. Status code: {response.status_code}. Server response: {response.text}")
        restockable_category_codes: list = response.json()
        
        item_codes = list({
            (
                item.read_product_key if item.read_product_key is not None else None,
                item.product.category.code if item.product and item.product.category else None
            )
            for item in message.items
            if not (
                item.read_product_key is None and 
                (item.product is None or item.product.category is None)
            )
        })

        for product_code, category_code in item_codes:
            if category_code in restockable_category_codes:
                logging.info(f"Generating predictions for category code '{category_code}'")

                response = request_tools.send_request_with_retries("get", f"{self.historics_endpoint}by-category-code/{category_code}", stop_event=self.stop_event)
                if response is None:
                    raise Exception(f"Failed to historic for category_code '{category_code}'. There was no response from server")
                if response.status_code != 200:
                    logging.error(f"Failed to historic for category_code '{category_code}'. Status code: {response.status_code}. Server response: {response.text}")
                    continue
                json_response = response.json()

                historic_data = []
                for json in json_response:
                    date = datetime.fromisoformat(json['date'])
                    quantity = float(json['quantity'])
                    historic_data.append((date, quantity))

                print(len(historic_data))
                predicted_dates = predict_next_purchase_dates(historic_data, PREDICT_DAYS_AHEAD)
                if not predicted_dates:
                    logging.info(f"No predicted dates for the next {PREDICT_DAYS_AHEAD} days")
                    return
                raw_predictions = predict_next_purchase_quantities(historic_data, predicted_dates)
                
                prediction = PredictionCreate(
                    category_code=str(category_code),
                )
                for date, quantity in raw_predictions:
                    prediction.items.append(
                        PredictionItemCreate(
                            date=date,
                            quantity=quantity
                        )
                    )

                response = request_tools.send_request_with_retries("post", f"{self.predictions_endpoint}", prediction.model_dump(mode='json'), stop_event=self.stop_event)
                if response is None:
                    raise Exception(f"Cannot post prediction. There was no response from server")
                if response.status_code == 200:
                    logging.info(f"Prediction for category code '{category_code}' created successfully")
                else:
                    logging.error(f"Failed to create prediction for category code '{category_code}'. Status code: {response.status_code}. Server response: {response.text}")

            if product_code in restockable_product_codes:
                logging.info(f"Generating predictions for product code '{product_code}'")

                response = request_tools.send_request_with_retries("get", f"{self.historics_endpoint}by-product-code/{product_code}", stop_event=self.stop_event)
                if response is None:
                    raise Exception(f"Failed to historic for {product_code}. There was no response from server")
                if response.status_code != 200:
                    logging.error(f"Failed to historic for {product_code}. Status code: {response.status_code}. Server response: {response.text}")
                    continue
                json_response = response.json()

                historic_data = []
                for json in json_response:
                    date = datetime.fromisoformat(json['date'])
                    quantity = float(json['quantity'])
                    historic_data.append((date, quantity))

                predicted_dates = predict_next_purchase_dates(historic_data, PREDICT_DAYS_AHEAD)
                if not predicted_dates:
                    logging.info(f"No predicted dates for the next {PREDICT_DAYS_AHEAD} days")
                    return
                raw_predictions = predict_next_purchase_quantities(historic_data, predicted_dates)
                
                prediction = PredictionCreate(
                    product_key=product_code,
                )
                for date, quantity in raw_predictions:
                    prediction.items.append(
                        PredictionItemCreate(
                            date=date,
                            quantity=quantity
                        )
                    )

                response = request_tools.send_request_with_retries("post", f"{self.predictions_endpoint}", prediction.model_dump(mode='json'), stop_event=self.stop_event)
                if response is None:
                    raise Exception(f"Cannot post prediction. There was no response from server")
                if response.status_code == 200:
                    logging.info(f"Prediction for product code '{product_code}' created successfully")
                else:
                    logging.error(f"Failed to create prediction for product code '{product_code}'. Status code: {response.status_code}. Server response: {response.text}")
        
        logging.info("Ready for next message") 

    def error_callback(self, error: Exception, _):        
        if isinstance(error, ValueError):
            logging.error(f"Could not find product data: {error}")
        if isinstance(error, JSONDecodeError):
            logging.error(f"Could not decode message: {error}")
        elif isinstance(error, ValidationError):
            logging.error(f"Received message format was not expected: {error}")
        else:
            logging.error(f"An unexpected error ({error.__class__.__name__}) occurred: {error}")
        
    def start(self):
        self.consumer.start(self.input_queue, self.callback, Purchase, self.error_callback)

    def stop(self):
        self.consumer.stop()

if __name__ == '__main__':
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL']

    parser = argparse.ArgumentParser(description="Purchase prediction service.")
    parser.add_argument('--logging', default='ERROR', choices=[level.lower() for level in LOG_LEVELS], help='Set logging level')
    args = parser.parse_args()

    logging.basicConfig(level=args.logging.upper())

    broker = typed_messaging.PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))
    
    restockables_endpoint = os.getenv('RESTOCKABLES_ENDPOINT','')
    if not restockables_endpoint.strip():
        logging.error("Restockables endpoint was not provided")
        sys.exit(1)
        
    historics_endpoint = os.getenv('HISTORICS_ENDPOINT','')
    if not historics_endpoint.strip():
        logging.error("Historics endpoint was not provided")
        sys.exit(1)
        
    predictions_endpoint = os.getenv('PREDICTIONS_ENDPOINT','')
    if not predictions_endpoint.strip():
        logging.error("Predictions endpoint was not provided")
        sys.exit(1)

    node = PurchasePredictorNode(
        restockables_endpoint,
        historics_endpoint,
        predictions_endpoint,
        broker.get_consumer(), 
        broker.ensure_queue(os.getenv('PURCHASE_PREDICTOR_INPUT_QUEUE', '')))

    try:
        logging.info("Node succesfully initialized")
        node.start()
    except KeyboardInterrupt:
        logging.info("Shutdown initiated by user (Ctrl+C)")
    finally:
        node.stop()
        sys.exit(0)