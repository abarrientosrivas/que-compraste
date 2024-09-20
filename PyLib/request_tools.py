import requests
import time
import logging
from requests.exceptions import ConnectionError, Timeout
from threading import Event

def send_request_with_retries(method: str, url: str, json_data = None, params: dict = None, stop_event: Event = None) -> requests.Response | None:
    wait_times = [0, 5, 10, 15, 30, 45, 60]
    retry_count = 0

    while stop_event is None or not stop_event.is_set():
        try:
            if method.lower() == 'get':
                return requests.get(url, params=params)
            elif method.lower() == 'post':
                return requests.post(url, json=json_data, params=params)
            elif method.lower() == 'put':
                return requests.put(url, json=json_data, params=params)
            elif method.lower() == 'delete':
                return requests.delete(url, params=params)
            else:
                raise ValueError("Method not supported.")

        except (ConnectionError, Timeout) as e:
            if retry_count < len(wait_times):
                wait_time = wait_times[retry_count]
            else:
                wait_time = 60

            logging.warning(f"Connection failed: {e}. Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
            retry_count += 1