import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ComprasService } from '../compras.service';
import { CommonModule } from '@angular/common';
import { ProductSearchComponent } from '../product-search/product-search.component';
import { FormsModule } from '@angular/forms';
import { log } from 'echarts/types/src/util/log.js';

@Component({
  selector: 'app-ver-compra',
  standalone: true,
  imports: [CommonModule, ProductSearchComponent, FormsModule],
  templateUrl: './ver-compra.component.html',
  styleUrl: './ver-compra.component.css',
})
export class VerCompraComponent {
  constructor(private comprasService: ComprasService) {}

  private activatedRoute = inject(ActivatedRoute);
  compraId = this.activatedRoute.snapshot.params['compraId'];
  compra: any;
  compra_backup: any;
  isEditMode = false;
  selectedItem: any; // editar producto

  ngOnInit() {
    this.comprasService.getCompraById(this.compraId).subscribe({
      next: (data) => {
        this.compra = data;
        console.log('Respuesta del servidor:', data);
      },
      error: (error) => {
        console.error('Error al hacer la petición:', error);
      },
      complete: () => {
        console.log('Petición completada');
      },
    });
  }

  editarCompra() {
    this.compra_backup = JSON.parse(JSON.stringify(this.compra));
    this.isEditMode = true;
  }

  convertToInt(value: string): number {
    return parseInt(value, 10);
  }

  onProductSelected(event: any) {
    const index = this.compra.items.findIndex(
      (item: any) => item === this.selectedItem
    );
    if (index !== -1) {
      console.log('Elemento actual: ', this.selectedItem);
      this.compra.items[index].read_product_text = event.product.title;
      this.compra.items[index].read_product_key = event.code;
      this.compra.items[index].product_id = event.id;
    }

    console.log('Evento recibido de product-search: ', event);
  }

  get fechaFormateada() {
    if (!this.compra && !this.compra.date) {
      return null;
    }
    const fecha = new Date(this.compra.date);
    return fecha.toLocaleDateString();
  }

  get horaFormateada() {
    if (!this.compra && !this.compra.date) {
      return;
    }
    const hora = new Date(this.compra.date);
    return hora.toLocaleTimeString('es-ES', {
      hour: 'numeric',
      minute: 'numeric',
    });
  }

  guardarCambios() {
    console.log('Cambios guardados:', this.compra);
    this.comprasService.updateCompra(this.compra.id, this.compra).subscribe({
      next: (data) => {
        console.log('Respuesta del servidor:', data);
        //this.compra = data; cuando se actualice la compra en el backend descomentar
      },
      error: (error) => {
        console.error('Error al hacer la petición:', error);
      },
      complete: () => {
        console.log('Petición completada');
      },
    });
    this.isEditMode = false;
  }

  cancelar() {
    this.isEditMode = false;
    this.compra = this.compra_backup;
  }

  seleccionarItem(item: any) {
    this.selectedItem = item;
  }

  onValueChange(value: number, index: number) {
    this.compra.items[index].total = value * this.compra.items[index].quantity;
    this.compra.total = this.compra.items.reduce(
      (sum: any, item: { total: any }) => sum + item.total,
      0
    );
  }

  onQuantityChange(quantity: number, index: number) {
    this.compra.items[index].total = quantity * this.compra.items[index].value;
    this.compra.total = this.compra.items.reduce(
      (sum: any, item: { total: any }) => sum + item.total,
      0
    );
  }
}
