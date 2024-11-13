import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

@Injectable({
  providedIn: 'root',
})
export class ReportesService {
  constructor(private http: HttpClient) {}
  private baseUrl = environment.apiUrl + "/expenses";

  getTotalsByCategory(startDate: string, endDate: string) : Observable<any> {    
    // const requestBody = [418,2073,4528];
    const requestBody = [413,730];

    return this.http.post<any>(
      `${this.baseUrl}/all-purchases/`,
      requestBody
    );
  }
}
