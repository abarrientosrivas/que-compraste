import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ProductsService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  search(product_code: string): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/product_codes/?lookahead=${product_code}`
    );
  }

  getProductCodes(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/purchase_items/product_codes/`);
  }

  getHistoricByProductCode(product_code: string): Observable<any[]> {
    return this.http.get<any[]>(
      `${this.apiUrl}/historics/by-product-code/${product_code}`
    );
  }

  getLastPredictionByProductCode(product_code: string): Observable<any> {
    return this.http.get<any>(
      `${this.apiUrl}/predictions/by-product-code/${product_code}`
    );
  }
}
