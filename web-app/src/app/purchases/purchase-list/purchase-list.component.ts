import { Component, OnInit } from '@angular/core';
import { ComprasService } from '../shared/compras.service';
import { Router } from '@angular/router';
import { RouterLink } from '@angular/router';
import { TableModule } from 'primeng/table';
import { CommonModule } from '@angular/common';
import { BadgeModule } from 'primeng/badge';
import { ButtonModule } from 'primeng/button';


@Component({
  selector: 'purchase-list',
  standalone: true,
  imports: [TableModule, CommonModule, RouterLink, BadgeModule, ButtonModule],
  templateUrl: './purchase-list.component.html',
  styleUrls: ['./purchase-list.component.css'],
  providers:[ComprasService]
})
export class PurchaseListComponent implements OnInit {
  constructor(private comprasService: ComprasService, private router: Router) {}

  purchases!: any[];
  loading = true;

  navigateToPurchase(id: string): void {
    this.router.navigate(['/compras', id]);
  }

  formatCurrency(value: number): string {
    return `$${value.toLocaleString('es-AR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }  

  ngOnInit(): void {
    this.comprasService.getAll().subscribe({
      next: (data: any) => {
        this.purchases = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error al hacer la petición:', error);
        this.loading = false;
      },
      complete: () => {
        console.log('Petición completada');
      },
    });
  }

  identify(index: number, purchase: any) {
    return purchase.id;
  }

  fechaFormateada(date: any) {
    const fecha = new Date(date);
    const options: Intl.DateTimeFormatOptions = {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    };
    return fecha.toLocaleDateString('es-AR', options);
  }
}
