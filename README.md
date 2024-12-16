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