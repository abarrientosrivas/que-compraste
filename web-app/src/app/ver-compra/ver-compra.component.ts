import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ComprasService } from '../compras.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-ver-compra',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ver-compra.component.html',
  styleUrl: './ver-compra.component.css',
})
export class VerCompraComponent {
  constructor(private comprasService: ComprasService) {}

  private activatedRoute = inject(ActivatedRoute);
  compraId = this.activatedRoute.snapshot.params['compraId'];
  compra: any;

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

  convertToInt(value: string): number {
    return parseInt(value, 10);
  }
}
