import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ReportesService {
  constructor(private http: HttpClient) {}
  private baseUrl = environment.apiUrl;

  getSubcategories(categoryCode: number): Observable<any> {
    const url = `${this.baseUrl}/categories/`;
    const params = new HttpParams().set('code', categoryCode);
    return this.http.get<any[]>(url, { params: params });
  }

  getPurchasesByCategory(
    category: number,
    startDate: string,
    endDate: string
  ): Observable<any> {
    const url = `${this.baseUrl}/purchases/`;
    const params = new HttpParams()
      .set('category_code', category)
      .set('start_date', startDate)
      .set('end_date', endDate);

    return this.http.get<any>(url, { params: params });
  }

  getRootCategoriesWithPurchases(
    startDate?: string,
    endDate?: string
  ): Observable<any> {
    const url = `${this.baseUrl}/categories/`;
    if (!startDate || !endDate) {
      return this.http.get<any[]>(url);
    }

    const params = new HttpParams()
      .set('start_date', startDate)
      .set('end_date', endDate);

    return this.http.get<any[]>(url, { params: params });
  }

  getTotalsBySubcategory(startDate: string, endDate: string, codes: any) {
    const params = new HttpParams()
      .set('start_date', startDate)
      .set('end_date', endDate);
    return this.http.post<any>(
      `${this.baseUrl}/expenses/all-purchases/`,
      codes,
      { params: params }
    );
  }

  getTotalsByCategory(startDate: string, endDate: string): Observable<any> {
    const params = new HttpParams()
      .set('start_date', startDate)
      .set('end_date', endDate);
    return new Observable((observer) => {
      this.getRootCategoriesWithPurchases(startDate, endDate).subscribe({
        next: (data: any[]) => {
          console.log('Respuesta del servidor:', data);
          this.http
            .post<any>(
              `${this.baseUrl}/expenses/all-purchases/`,
              data.map((item) => item.code),
              {
                params: params,
              }
            )
            .subscribe({
              next: (response) => {
                observer.next(response);
                observer.complete();
              },
              error: (error) => {
                console.error('Error en el post request:', error);
                observer.error(error);
              },
            });
        },
        error: (error) => {
          console.error('Error al hacer la petición:', error);
          observer.error(error);
        },
      });
    });
  }

  getPurchasesByRangeDate(startDate: string, endDate: string): Observable<any> {
    const url = `${this.baseUrl}/purchases/`;
    const params = new HttpParams()
      .set('start_date', startDate)
      .set('end_date', endDate);

    return this.http.get<any[]>(url, { params: params });
  }
}
