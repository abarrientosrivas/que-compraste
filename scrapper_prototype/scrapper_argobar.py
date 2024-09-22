from bs4 import BeautifulSoup
import sys
import json
from crawler_prototype.crawler_argobar import get_page_source


def get_datos_efiscal(cuit):
    page_source = get_page_source(cuit)
    soup = BeautifulSoup(page_source, 'html.parser')
    result = {}

    nombre_fantasia_strong = soup.find('strong', string='Nombre de Fantasía ')
    if nombre_fantasia_strong:
        nombre_fantasia = nombre_fantasia_strong.find_next_sibling('p')
        result['nombre_fantasia'] = nombre_fantasia.get_text(strip=True)
    else:
        result['nombre_fantasia'] = None

    return json.dumps(result, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 -m 'scrapper_prototype.scrapper_argobar' <cuit>")
        sys.exit(1)

    cuit = sys.argv[1]

    entidad_fiscal = get_datos_efiscal(cuit)
    print(entidad_fiscal)
