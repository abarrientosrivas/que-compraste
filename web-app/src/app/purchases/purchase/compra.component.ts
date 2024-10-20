import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ComprasService } from '../shared/compras.service';
import { CommonModule } from '@angular/common';
import { ProductSearchComponent } from '../../product-search/product-search.component';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-ver-compra',
  standalone: true,
  imports: [CommonModule, ProductSearchComponent, FormsModule],
  templateUrl: './compra.component.html',
  styleUrl: './compra.component.css',
})
export class CompraComponent {
  constructor(private comprasService: ComprasService) {}

  private activatedRoute = inject(ActivatedRoute);
  compraId = this.activatedRoute.snapshot.params['compraId'];
  compra: any;

  ngOnInit() {
    this.comprasService.getCompraById(this.compraId).subscribe({
      next: (data: any) => {
        data.items.sort((a: any, b: any) => a.id - b.id);
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

  convertToInt(value: string): number {
    return parseInt(value, 10);
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
}
