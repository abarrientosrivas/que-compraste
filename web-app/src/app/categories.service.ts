import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class CategoriesService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  // search(product_code: string): Observable<any[]> {
  //   return this.http.get<any[]>(
  //     `${this.apiUrl}/categories/?lookahead=${product_code}`
  //   );
  // }

  getCategoryCodes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/restockables/categories/`);
  }

  getCategories(code?: string): Observable<any[]> {
    const url = code ? `${this.apiUrl}/categories/?code=${code}` : `${this.apiUrl}/categories/`;
    return this.http.get<any[]>(url);
  }

  // getHistoricByProductCode(product_code: string): Observable<any[]> {
  //   return this.http.get<any[]>(
  //     `${this.apiUrl}/historics/by-product-code/${product_code}`
  //   );
  // }

  // getLastPredictionByProductCode(product_code: string): Observable<any> {
  //   return this.http.get<any>(
  //     `${this.apiUrl}/predictions/by-product-code/${product_code}`
  //   );
  // }
}