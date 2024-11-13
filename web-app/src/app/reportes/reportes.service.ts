import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ReportesService {
  constructor(private http: HttpClient) {}
  private baseUrl = 'http://localhost:8000';

  getPurchases(startDate: string, endDate: string) {
    const url = `${this.baseUrl}/purchases/`;
    const params = new HttpParams()
      .set('start_date', startDate)
      .set('end_date', endDate);
    return this.http.get<any[]>(url, { params: params });
  }

  getRootCategoriesWithPurchases(
    startDate: string,
    endDate: string
  ): Observable<any> {
    const url = `${this.baseUrl}/categories/`;
    const params = new HttpParams()
      .set('start_date', startDate)
      .set('end_date', endDate);

    return this.http.get<any[]>(url, { params: params });
  }

  getTotalsByCategory(startDate: string, endDate: string): Observable<any> {
    return new Observable((observer) => {
      this.getRootCategoriesWithPurchases(startDate, endDate).subscribe({
        next: (data: any[]) => {
          console.log('Respuesta del servidor:', data);
          this.http
            .post<any>(
              `${this.baseUrl}/expenses/all-purchases/`,
              data.map((item) => item.code)
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
