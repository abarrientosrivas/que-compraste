import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../environments/environment';

export interface Category {
    id: number;
    name: string;
    name_es_es: string;
    description?: string;
}

export interface Product {
    id: number;
    title: string;
    description?: string;
    img_url?: string;
    category?: Category;
  }

export interface PurchaseItemCart {
    read_product_key?: string;
    read_product_text?: string;
    quantity?: number;
    value?: number;
    total?: number;
    product?: Product;
}

export interface Cart {
    date: Date;
    items: PurchaseItemCart[];
}

@Injectable({
    providedIn: 'root',
})
export class CartsService {
    private apiUrl = environment.apiUrl;

    constructor(private http: HttpClient) { }

    getCarts(): Observable<any[]> {
        return this.http.get<any[]>(`${this.apiUrl}/predictions/suggested_carts/`);
    }
}
