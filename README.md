# QuéCompraste?
## Seguimiento y análisis de compras

QuéCompraste? es un sitio web diseñado para asistir y simplificar la planificación financiera, ofreciendo una solución integrada para esta actividad. La plataforma permite cargar y guardar en la nube fácilmente los detalles de las compras escaneando recibos; para luego proporcionar información, estadísticas y estimaciones de gastos a partir de los datos acumulados. Estas herramientas ayudarán a entender mejor los patrones de gasto para una toma de decisiones financieras más informada.

Para preguntas, comentarios o sugerencias sobre el proyecto QuéCompraste? contactar a Alexis Barrientos Rivas (alexisbarrientos97@gmail.com) o a Ariel Sepulveda (ariel.sepulveda.ar@gmail.com).

### Atribuciones y Reconocimientos
Este proyecto utiliza el modelo `donut-receipts-extract` desarrollado por Adam Codd en Hugging Face. El uso de este modelo sigue bajo los términos de la licencia Creative Commons Attribution Non-Commercial 4.0 (CC BY-NC 4.0). Para más detalles sobre el modelo y su licencia, visite el [repositorio del modelo](https://huggingface.co/AdamCodd/donut-receipts-extract).

## Contenido
- API: Aplicación FastAPI escrita en Python. Es el backend de nuestro proyecto y el único punto de comunicación desde el frontend al servidor.
- Docs: Documentación referente al proyecto, su desarrollo e investigación.
- PyLib: Librerías escritas en Python, utilizadas en API y en PyNodes.
- PyNodes: Servicios escritos en Python y comunicados por RabbitMQ. Realizan distintas tareas requeridas por el proyecto.
- web-app: Frontend de la aplicación para interacción del usuario con la plataforma. Escrito en Angular.

## Instrucciones
**Requisitos generales:** 
- Tener instalado y configurado RabbitMQ para usar como message broker.
- Configurar un archivo .env en base al .env.example

### API
**Requisitos** Python 3.10+
1. Instale con pip las librerias en API/requirements.txt
2. Asigne un token con permisos de --view_receipts en el .env (utilice el script create_node_token.py)
3. Ejecute la API con el comando ```uvicorn API.main:app```

### Frontend
**Requisitos** Node.js y npm
1. Ubíquese en la carpeta web-app
2. Instale las dependencias con el comando ```npm install```
3. Utilice los comandos ```npm start``` o ```npm run build``` para probar o compilar la aplicación

### Nodo buscador de entidades
**Requisitos** Python 3.10+
1. Asigne un token con --crawl_limit en el .env (utilice el script create_node_token.py)
2. Instale con pip las librerias necesarias
3. Asigne un token con permisos de --view_receipts en el .env (utilice el script create_node_token.py)
4. Ejecute el nodo con el comando ```python -m PyNodes.entity_finder_node```

### Nodo buscador de productos
**Requisitos** Python 3.10+
1. Asigne un token con --crawl_limit en el .env (utilice el script create_node_token.py)
2. Instale con pip las librerias necesarias
3. Ejecute el nodo con el comando ```python -m PyNodes.product_finder_node```

### Nodo clasificador de productoos
**Requisitos** Python 3.10
1. Instale con pip las librerias necesarias
2. Inicialice la base de datos ChromaDB con el comando ```python -m PyNodes.product_classifier_node --init```
*chequear comandos ```--sync``` y ```--add_es_es```*
3. Ejecute el nodo con el comando ```python -m PyNodes.product_classifier_node```

### Nodo predictor de compras
**Requisitos** Python 3.10+
1. Instale con pip las librerias necesarias
2. Ejecute el nodo con el comando ```python -m PyNodes.purchase_predictor_node```

### Nodo imagen a compra (donut)
**Requisitos** Python 3.10+
1. Asigne un token con permisos de --view_receipts en el .env (utilice el script create_node_token.py)
2. Instale con pip las librerias necesarias
3. Ejecute el nodo con el comando  ```python -m PyNodes.image_to_compra_node```

### Nodo imagen a compra (donut)
**Requisitos** Python 3.10+, GPU dedicada con 20gb de memoria de video libres
1. Asigne un token con permisos de --view_receipts en el .env (utilice el script create_node_token.py)
2. Instale con pip las librerias necesarias
3. Ejecute el nodo con el comando ```python -m PyNodes.qwen_receipt_reader_node```