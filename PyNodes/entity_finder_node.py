import argparse
import logging
import threading
import os
import sys
import json
import pytesseract
import time
import random
from PyLib.typed_messaging import PydanticMessageBroker, PydanticExchangePublisher, PydanticQueueConsumer
from pydantic import ValidationError
from json.decoder import JSONDecodeError
from dotenv import load_dotenv
from pydantic import BaseModel
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from io import BytesIO
from PIL import Image

load_dotenv()

TASK_DELAY = os.getenv("CRAWLERS_TASK_DELAY",10)

def create_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    #chrome_options.add_argument('--enable-logging')
    #chrome_options.add_argument('--v=1') 
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def canvas_to_str(canvas):
    captcha_png = canvas.screenshot_as_png
    image_data = BytesIO(captcha_png)
    image = Image.open(image_data)
    return pytesseract.image_to_string(image, config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')

class EntityIdentificationMessage(BaseModel):
    identification: str

class ProductFinderNode:
    def __init__(self, consumer: PydanticQueueConsumer, publisher: PydanticExchangePublisher, input_queue: str):
        self.consumer = consumer
        self.publisher = publisher
        self.input_queue = input_queue
        self.stop_event = threading.Event()
        self.driver = create_driver()

    def get_page_source(self, cuit):
        search_url = 'https://www.argentina.gob.ar/aaip/datospersonales/reclama'
        self.driver.get(search_url)
        cuit_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@id='edit-razon']")))
        cuit_input.send_keys(cuit)
        cuenta_element = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//div[@class='form-item form-item-captcha-response form-type-textfield form-group']")))
        cuenta = cuenta_element.text.split('Cuál es el resultado *')[1].strip().split('=')[0]
        cuenta_resuelta = eval(cuenta)
        resultado_input = self.driver.find_element(By.XPATH, "//input[@id='edit-captcha-response']")
        resultado_input.send_keys(cuenta_resuelta)
        boton_buscar = self.driver.find_element(By.XPATH, "//button[@id='edit-submit']")
        boton_buscar.click()

        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//table/tbody/tr[1]/td[last()]/a"))
            )
            element.click()
            counter = 0
            while True:
                captcha_str = canvas_to_str(WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//canvas[@id='captcha']"))))
                captcha_input = self.driver.find_element(By.XPATH, "//input[@id='cpatchaTextBox']")               
                self.driver.execute_script("arguments[0].value = arguments[1];", captcha_input, captcha_str)
                submit_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[@type='submit'][text()='Enviar']")))
                submit_button.click()                
                counter += 1
                try:
                    captcha_message = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@id='menssage_captcha']"))).text
                    
                    if captcha_message == "":
                        #print("Captcha resuelto correctamente.")
                        return self.driver.page_source

                    if captcha_message == "Por favor intrese el texto que aparece arriba" and counter > 5:
                        #print("Volviendo a intentar el captcha")
                        break

                except NoSuchElementException:
                    #print("Posiblemente se resolvió el CAPTCHA y la página cambió.")
                    return self.driver.page_source
                
                captcha_input.send_keys(Keys.CONTROL + "a")
                captcha_input.send_keys(Keys.BACKSPACE) 
        except TimeoutException:
            print("El boton 'Ver' no se cargó en el tiempo esperado")

    def get_datos_efiscal(self, cuit):
        page_source = self.get_page_source(cuit)
        soup = BeautifulSoup(page_source, 'html.parser')
        result = {}

        nombre_fantasia_strong = soup.find('strong', string='Nombre de Fantasía ')
        if nombre_fantasia_strong:
            nombre_fantasia = nombre_fantasia_strong.find_next_sibling('p')
            result['nombre_fantasia'] = nombre_fantasia.get_text(strip=True)
        else:
            result['nombre_fantasia'] = None

        email_h5 = soup.find('h5', string='Correo electrónico')
        if email_h5:
            email = email_h5.find_next_sibling('p')
            result['email'] = email.get_text(strip=True)
        else:
            result['email'] = None

        telefono_h5 = soup.find('h5', string='Teléfono')
        if telefono_h5:
            telefono = telefono_h5.find_next_sibling('p')
            result['telefono'] = telefono.get_text(strip=True)
        else:
            result['telefono'] = None

        domicilio_h5 = soup.find('h5', string='Domicilio')
        if domicilio_h5:
            domicilio = domicilio_h5.find_next_sibling('p')
            result['domicilio'] = domicilio.get_text(strip=True)
        else:
            result['domicilio'] = None

        return json.dumps(result, indent=4, ensure_ascii=False)

    def callback(self, message: EntityIdentificationMessage):
        received_identification =  message.identification.strip()
        if not received_identification:
            logging.info(f"Ignoring empty message")

        logging.info(f"Processing an entity identification: {received_identification}")

        print(self.get_datos_efiscal(message.identification))
        
        logging.info(f"Complying with crawler delay")
        time.sleep(TASK_DELAY + random.uniform(0, 2)) 

    def error_callback(self, error: Exception):        
        if isinstance(error, ValueError):
            logging.error(f"Could not find entity data: {error}")
        if isinstance(error, JSONDecodeError):
            logging.error(f"Could not decode message: {error}")
        elif isinstance(error, ValidationError):
            logging.error(f"Received message format was not expected: {error}")
        else:
            logging.error(f"An unexpected error ({error.__class__.__name__}) occurred: {error}")
        
    def start(self):
        self.consumer.start(self.input_queue, self.callback, EntityIdentificationMessage, self.error_callback)

    def stop(self):
        self.stop_event.set()
        self.consumer.stop()
        if self.driver:
            self.driver.quit()

if __name__ == '__main__':
    LOG_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL', 'FATAL']

    parser = argparse.ArgumentParser(description="Entity data retriever service.")
    parser.add_argument('--logging', default='ERROR', choices=[level.lower() for level in LOG_LEVELS], help='Set logging level')
    args = parser.parse_args()

    logging.basicConfig(level=args.logging.upper())

    broker = PydanticMessageBroker(os.getenv('RABBITMQ_CONNECTION_STRING', 'amqp://guest:guest@localhost:5672/'))

    node = ProductFinderNode(
        broker.get_consumer(), 
        broker.get_publisher(), 
        broker.ensure_queue(os.getenv('ENTITY_FINDER_INPUT_QUEUE', '')))

    try:
        logging.info("Node succesfully initialized")
        node.start()
    except KeyboardInterrupt:
        logging.info("Shutdown initiated by user (Ctrl+C)")
    finally:
        node.stop()
        sys.exit(0)