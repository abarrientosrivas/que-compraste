import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ComprasService {
  constructor(private http: HttpClient) {}

  private baseUrl = environment.apiUrl;

  getAll(): Observable<any[]> {
    const url = `${this.baseUrl}/purchases`;
    return this.http.get<any[]>(url);
  }

  getCompraById(id: number) {
    const url = `${this.baseUrl}/purchases/${id}`;
    return this.http.get(url);
  }

  updatePurchase(id: number, data: any) {
    const url = `${this.baseUrl}/purchases/${id}`;
    return this.http.put(url, {
      ...data,
    });
  }

  updateProductCode(productId: number, itemId: number, productCode: any) {
    const url = `${this.baseUrl}/purchases/${productId}`;
    return this.http.put(url, { "items": [{"id": itemId, "read_product_key": productCode, "product_id": null}]})
  };

  getReceiptImage(imagePath: string) {
    const url = `${imagePath}`;
    const token = 'a9063f0da4047d45f9511e6496653829ddf3c3a3b8041f79d0ca997605f2c4b2'
    return this.http.get(url, {
      headers: {
        'Authorization': `Bearer ${token}`
      },
      responseType: 'blob'
    });
  }

  getExpensesByCategory(purchaseId: number): Observable<any[]> {
    const url = `${this.baseUrl}/expenses/purchase/${purchaseId}`;
    return this.http.get<any[]>(url);
  }

}
