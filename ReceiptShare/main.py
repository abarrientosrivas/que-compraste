from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/receipt")
async def receipt(request: Request):
    return templates.TemplateResponse("receipt.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_images(images: list[UploadFile] = File(...)):
    filenames = [image.filename for image in images]
    response_content = "<div>Recibidas las imágenes:</div>"
    response_content += "<ul>" + "".join(f"<li>{filename}</li>" for filename in filenames) + "</ul>"
    return response_content

@app.get("/{path:path}")
async def redirect_to_receipt(path: str):
    return RedirectResponse(url="/receipt")
