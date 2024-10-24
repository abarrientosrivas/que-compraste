import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ComprasService } from '../shared/compras.service';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'purchase-list',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './purchase-list.component.html',
})
export class PurchaseListComponent implements OnInit {
  constructor(private comprasService: ComprasService) {}

  purchases: any[] = [];

  ngOnInit(): void {
    this.comprasService.getAll().subscribe({
      next: (data: any) => {
        this.purchases = data;
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

  identify(index: number, purchase: any) {
    return purchase.id;
  }

  deletePurchase(id: number) {
    console.log('Test: Eliminando compra con id:', id);
  }

  fechaFormateada(date: any) {
    const fecha: any = new Date(date);
    return fecha.toLocaleDateString("es-AR");
  }

  horaFormateada(date: any) {
    const hora = new Date(date);
    return hora.toLocaleTimeString('es-ES', {
      hour: 'numeric',
      minute: 'numeric',
    });
  }
}
