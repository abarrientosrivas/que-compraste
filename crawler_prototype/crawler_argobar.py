from io import BytesIO
import sys
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from PIL import Image
import pytesseract

def create_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    #chrome_options.add_argument('--enable-logging')
    #chrome_options.add_argument('--v=1') 
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def get_page_source(cuit):
    try:
        driver = create_driver()
        search_url = 'https://www.argentina.gob.ar/aaip/datospersonales/reclama'
        driver.get(search_url)
        cuit_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@id='edit-razon']")))
        cuit_input.send_keys(cuit)
        cuenta_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//div[@class='form-item form-item-captcha-response form-type-textfield form-group']")))
        cuenta = cuenta_element.text.split('Cuál es el resultado *')[1].strip().split('=')[0]
        cuenta_resuelta = resolver_cuenta(cuenta)
        resultado_input = driver.find_element(By.XPATH, "//input[@id='edit-captcha-response']")
        resultado_input.send_keys(cuenta_resuelta)
        boton_buscar = driver.find_element(By.XPATH, "//button[@id='edit-submit']")
        boton_buscar.click()

        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//table/tbody/tr[1]/td[last()]/a"))
            )
            element.click()
            counter = 0
            while True:
                captcha_str = canvas_to_str(WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//canvas[@id='captcha']"))))
                captcha_input = driver.find_element(By.XPATH, "//input[@id='cpatchaTextBox']")               
                driver.execute_script("arguments[0].value = arguments[1];", captcha_input, captcha_str)
                submit_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[@type='submit'][text()='Enviar']")))
                submit_button.click()                
                counter += 1
                try:
                    captcha_message = WebDriverWait(driver, 5).until(
                        EC.presence_of_element_located((By.XPATH, "//div[@id='menssage_captcha']"))).text
                    
                    if captcha_message == "":
                        print("Captcha resuelto correctamente.")
                        return driver.page_source

                    if captcha_message == "Por favor intrese el texto que aparece arriba" and counter > 5:
                        print("Volviendo a intentar el captcha")
                        break

                except Exception as e:
                    print("Posiblemente se resolvió el CAPTCHA y la página cambió.")
                    time.sleep(5)
                    return driver.page_source
                
                captcha_input.send_keys(Keys.CONTROL + "a")
                captcha_input.send_keys(Keys.BACKSPACE) 
        except TimeoutException:
            print("El boton 'Ver' no se cargó en el tiempo esperado")
        
    finally:
        driver.quit()

def canvas_to_str(canvas):
    captcha_png = canvas.screenshot_as_png
    image_data = BytesIO(captcha_png)
    image = Image.open(image_data)
    return pytesseract.image_to_string(image, config='--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789')

def resolver_cuenta(cuenta):
    return eval(cuenta)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python crawler_argobar.py <cuit>")
        sys.exit(1)

    cuit = sys.argv[1]

    html_content = get_page_source(cuit)
    print(html_content)
