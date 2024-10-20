import { Component, EventEmitter, Output } from '@angular/core';
import { FormControl, FormsModule, ReactiveFormsModule } from '@angular/forms';
import { debounceTime, switchMap } from 'rxjs/operators';
import { ProductsService } from '../products.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-product-search',
  standalone: true,
  imports: [FormsModule, CommonModule, ReactiveFormsModule],
  templateUrl: './product-search.component.html',
  styleUrl: './product-search.component.css',
})
export class ProductSearchComponent {
  query = '';
  searchControl = new FormControl();
  selectedItem = new FormControl('');
  results: any;

  constructor(private productsService: ProductsService) {
    this.searchControl.valueChanges
      .pipe(
        debounceTime(300),
        switchMap((value) => this.productsService.search(value))
      )
      .subscribe((data) => {
        this.results = data;
      });
  }

  @Output() productSelected = new EventEmitter<any>();

  onProductSelected() {
    const selected = this.selectedItem.value;
    this.productSelected.emit(selected);
  }

  search() {
    this.productsService.search(this.query).subscribe((data) => {
      this.results = data;
      console.log('Respuesta del servidor:', data);
    },
    (error) => {
      console.error('Error fetching products', error);
      this.results = [];
    });
  }

  resetForm() {
    this.query = '';
    this.results = [];
  }
}
