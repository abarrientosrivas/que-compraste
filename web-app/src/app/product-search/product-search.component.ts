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

  constructor(private productsService: ProductsService) {}

  @Output() productSelected = new EventEmitter<any>();
  @Output() noResults = new EventEmitter<any>();
  @Output() productCode = new EventEmitter<any>();

  onProductSelected() {
    const selected = this.selectedItem.value;
    this.productSelected.emit(selected);
  }

  search() {
    this.productCode.emit(this.query)
    this.productSelected.emit(null)
    if (this.query.toString().length >= 3) {
      this.productsService.search(this.query.toString()).subscribe({
        next: (data) => {
          this.results = data;
          console.log('Respuesta del servidor:', data);
          if (data.length == 0)
            this.noResults.emit(true)
          else
            this.noResults.emit(false)
        },
        error: (error) => {
          console.error('Error al buscar producto', error);
          this.results = [];
        }
      });
    } else {
      this.results = []
      console.log("hola")
      this.productSelected.emit(null);
      this.noResults.emit(false)
    }
}

  resetForm() {
    this.query = '';
    this.results = [];
  }
}
