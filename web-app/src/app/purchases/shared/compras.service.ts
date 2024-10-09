import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ComprasService {
  constructor(private http: HttpClient) {}

  private baseUrl = 'http://127.0.0.1:8000';

  getAll(): Observable<any[]> {
    const url = `${this.baseUrl}/purchases`;
    return this.http.get<any[]>(url);
  }

  getCompraById(id: number) {
    const url = `${this.baseUrl}/purchases/${id}`;
    return this.http.get(url);
  }

  updateCompra(id: number, data: any) {
    const url = `${this.baseUrl}/purchases/${id}`;
    return this.http.put(url, {
      ...data,
    });
  }
}