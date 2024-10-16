import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class ReportesService {
  constructor(private http: HttpClient) {}
  private baseUrl = 'http://localhost:8000/expenses';

  getTotalsByCategory(startDate: string, endDate: string) : Observable<any> {    
    // const requestBody = [418,2073,4528];
    const requestBody = [413,730];

    return this.http.post<any>(
      `${this.baseUrl}/all-purchases/`,
      requestBody
    );
  }
}
