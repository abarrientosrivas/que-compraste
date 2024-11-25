import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class TicketUploadService {
  constructor(private http: HttpClient) {}

  uploadFile(files: FileList): Observable<any> {
    const formData = new FormData();
    Array.from(files).forEach((file) => formData.append('files', file));
    return this.http.post(environment.apiUrl + '/upload/', formData, {
      reportProgress: true,
      observe: 'events',
    });
  }

  getReceiptsStatus(): Observable<any> {
    return this.http.get(
      environment.apiUrl + '/receipts/waiting_and_processing/'
    );
  }

  getReceipt(receipt_id: number): Observable<any> {
    return this.http.get(environment.apiUrl + '/receipts/' + receipt_id);
  }

  getStatusUpdates(receiptId: number): Observable<any> {
    const url = `${environment.apiUrl}/receipts/${receiptId}/status_changes`;
    return new Observable((observer) => {
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        observer.next(event.data);
      };

      eventSource.onerror = (error) => {
        observer.error(error);
      };

      eventSource.onopen = () => {
        console.log('Connection established');
      };

      return () => {
        eventSource.close();
      };
    });
  }
}
