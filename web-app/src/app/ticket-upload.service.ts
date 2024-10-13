import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class TicketUploadService {
  constructor(private http: HttpClient) {}

  uploadFile(files: FileList): Observable<any> {
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append('files', file));
    return this.http.post('http://127.0.0.1:8000/upload/', formData, {
      reportProgress: true,
      observe: 'events',
    });
  }
}
