import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Injectable({
  providedIn: 'root',
})
export class ReportesService {
  constructor(private http: HttpClient) {}
  private baseUrl = 'http://localhost:8000/reportes';

  getTotalsByCategory(startDate: string, endDate: string) {
    return this.http.get<any>(
      `${this.baseUrl}/total-by-category?start_date=${startDate}&end_date=${endDate}`
    );
  }
}
