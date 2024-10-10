import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class TicketUploadService {
  constructor(private http: HttpClient) {}

  uploadFile(files: FileList) {
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append('files', file));
    return this.http.post('http://127.0.0.1:8000/upload/', formData);
  }
}
