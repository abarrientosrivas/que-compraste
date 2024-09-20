import os
import hashlib
import logging
import threading
import aiofiles
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, Request, HTTPException
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

MAX_FOLDER_SIZE = 20 * 1024 * 1024 * 1024 # 20 GB
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

@app.get("/recibos")
async def receipt(request: Request):
    return templates.TemplateResponse("receipt.html", {"request": request})

@app.post("/upload", response_class=HTMLResponse)
async def upload_files(request: Request, files: List[UploadFile] = File(...)):
    max_file_size = 16 * 1024 * 1024  # 16 MB
    ignored_files = 0

    with lock:
        if not files:
            return "<div>Ningún archivo recibido.</div>"
        
        current_folder_size = get_folder_size(files_dir)
        saved_files = []
        for file in files:
            if not (file.content_type.startswith("image") or file.content_type == "application/pdf"):
                ignored_files += 1
                await file.close()
                continue

            if file.size > max_file_size:
                ignored_files += 1
                await file.close()
                continue

            future_size = current_folder_size + file.size
            if future_size > MAX_FOLDER_SIZE:
                return "<div>Servidor en capacidad máxima.</div>"

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

        response_content = "<div>"
        if ignored_files > 0:
            response_content += f"<p>Archivos ignorados: {ignored_files}</p>"
        if not saved_files:
            response_content +="<p>Ningún archivo guardado.</p></div>"
            return response_content
        response_content += "<p>Archivos guardados:</p>"
        response_content += "<ul>" + "".join(f"<li>{filename}</li>" for filename in saved_files) + "</ul>"
        response_content += "<p><b>Gracias por tu aporte.</b></p>"
        response_content += "</div>"
        return response_content

@app.get("/recibos/status")
def get_status():
    full_path = os.path.abspath(files_dir)

    if not os.path.isdir(full_path):
        raise HTTPException(status_code=404, detail="Directory not found")

    total_size = 0
    file_count = 0

    for dirpath, _, filenames in os.walk(full_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                try:
                    file_count += 1
                    total_size += os.path.getsize(fp)
                except OSError:
                    continue

    total_size_gb = bytes_to_gb(total_size)

    return {
        "uploaded_files": file_count,
        "disk_gbs_used": total_size_gb
    }

def bytes_to_gb(size_in_bytes):
    """Convert bytes to gigabytes."""
    return size_in_bytes / (1024 ** 3)

@app.get("/{path:path}")
async def redirect_to_receipt(path: str):
    return RedirectResponse(url="/recibos")