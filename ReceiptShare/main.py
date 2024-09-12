import os
import hashlib
import logging
import threading
import aiofiles
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware
from typing import List

class CustomHeaderMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if 'text/html' in response.headers.get('Content-Type', ''):
            csp = "default-src 'self'; " \
                  "script-src 'self' https://unpkg.com; " \
                  "style-src 'self' 'unsafe-inline'; " \
                  "img-src 'self';"
            response.headers['Content-Security-Policy'] = csp
            response.headers['X-Content-Type-Options'] = "nosniff"
            response.headers['X-Frame-Options'] = "DENY"
            response.headers['Strict-Transport-Security'] = "max-age=31536000; includeSubDomains"
            response.headers['X-XSS-Protection'] = "1; mode=block"
        return response

lock = threading.Lock()
app = FastAPI()
app.add_middleware(CustomHeaderMiddleware)
templates = Jinja2Templates(directory="templates")

MAX_FOLDER_SIZE = 1024 * 1024 * 1024 # 1 GB
files_dir = "uploaded_files"
os.makedirs(files_dir, exist_ok=True)

def get_folder_size(folder):
    total_size = 0
    for dirpath, _, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return total_size

def generate_filename(sender_ip: str, original_filename: str):
    extension = original_filename.split('.')[-1]
    ip_hash = hashlib.sha256(sender_ip.encode()).hexdigest()
    short_hash = ip_hash[:16]
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    sequence = 1
    new_filename = f"{short_hash}-{timestamp}-{sequence}.{extension}"
    file_path = os.path.join(files_dir, new_filename)
    
    while os.path.exists(file_path):
        sequence += 1
        new_filename = f"{short_hash}-{timestamp}-{sequence}.{extension}"
        file_path = os.path.join(files_dir, new_filename)
    
    return new_filename

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse('icon.ico')

@app.get("/receipt")
async def receipt(request: Request):
    return templates.TemplateResponse("receipt.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_files(request: Request, files: List[UploadFile] = File(...)):
    max_file_size = 10 * 1024 * 1024  # 10 MB

    with lock:
        if not files:
            return "Ningún archivo recibido."
        
        current_folder_size = get_folder_size(files_dir)
        saved_files = []
        for file in files:
            if not (file.content_type.startswith("image") or file.content_type == "application/pdf"):
                await file.close()
                continue

            if file.size > max_file_size:
                await file.close()
                continue

            future_size = current_folder_size + file.size
            if future_size > MAX_FOLDER_SIZE:
                return "Servidor en capacidad máxima."

            try:
                filename = generate_filename(request.client.host, file.filename)
                file_path = os.path.join(files_dir, filename)
                async with aiofiles.open(file_path, 'wb') as buffer:
                    contents = await file.read()
                    await buffer.write(contents)
                saved_files.append(file.filename)
            except Exception as e:
                logging.error(f"Error saving file: {e}")

            await file.close()

        if not saved_files:
            return "Ningún archivo recibido."
        response_content = "<div>Archivos recibidos:</div>"
        response_content += "<ul>" + "".join(f"<li>{filename}</li>" for filename in saved_files) + "</ul>"
        return response_content

@app.get("/{path:path}")
async def redirect_to_receipt(path: str):
    return RedirectResponse(url="/receipt")
