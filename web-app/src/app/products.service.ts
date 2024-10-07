import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ProductsService {
  //private apiUrl = 'http://localhost:8000/products'; // Ajusta la URL según tu backend
  private apiUrl = 'http://localhost:8000'; // Ajusta la URL según tu backend

  constructor(private http: HttpClient) {}

  search(product_code: string): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/product_codes/?lookahead=${product_code}`
    );
  }
}
