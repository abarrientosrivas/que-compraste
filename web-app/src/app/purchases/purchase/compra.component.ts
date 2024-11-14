import { Component, inject } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { ComprasService } from '../shared/compras.service';
import { CommonModule } from '@angular/common';
import { ProductSearchComponent } from '../../product-search/product-search.component';
import { FormsModule } from '@angular/forms';
import { NgbPopoverModule, NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { ImageViewerModule } from 'ngx-image-viewer-3';
import { ChartModule } from 'primeng/chart';

@Component({
  selector: 'app-ver-compra',
  standalone: true,
  imports: [
    CommonModule,
    ProductSearchComponent,
    FormsModule,
    NgbPopoverModule,
    NgbTooltipModule,
    ImageViewerModule,
    ChartModule,
  ],
  templateUrl: './compra.component.html',
  styleUrl: './compra.component.css',
})
export class CompraComponent {
  constructor(
    private comprasService: ComprasService,
    private sanitizer: DomSanitizer
  ) {}

  private activatedRoute = inject(ActivatedRoute);
  compraId = this.activatedRoute.snapshot.params['compraId'];
  compra: any;
  data: any;
  data1: any = { labels: [], datasets: [{ data: [] }] };
  options: any;

  images: string[] = [];

  ngOnInit() {
    this.options = {
      responsive: true,
      radius: '75%',
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            usePointStyle: true,
            color: '#000000',
          },
        },
      },
    };

    this.comprasService.getCompraById(this.compraId).subscribe({
      next: (data: any) => {
        data.items.sort((a: any, b: any) => a.id - b.id);
        this.compra = data;

        this.images = [];
        if (this.compra.receipt && this.compra.receipt.image_url) {
          this.comprasService
            .getReceiptImage(this.compra.receipt.image_url)
            .subscribe({
              next: (blob: Blob) => {
                const imageUrl = URL.createObjectURL(blob);
                this.images.push(imageUrl);
                console.log('Respuesta del servidor:', blob);
              },
              error: (error) => {
                console.error('Error al hacer la petición:', error);
              },
              complete: () => {
                console.log('Petición completada');
              },
            });
        }
        console.log('Respuesta del servidor:', data);
      },
      error: (error) => {
        console.error('Error al hacer la petición:', error);
      },
      complete: () => {
        console.log('Petición completada');
        this.comprasService.getExpensesByCategory(this.compra.id).subscribe({
          next: (data: any[]) => {
            const filteredData = data.filter((element) => {
              return element[0].parent_id == null;
            });
            console.log('Respuesta del servidor:', filteredData);
            this.data1.labels = filteredData.map((element) => {
              return element[0].name;
            });
            this.data1.datasets[0].data = filteredData.map((element) => {
              return element[1];
            });
            this.data = { ...this.data1 };
            console.log(this.data1);
          },
          error: (error) => {
            console.error('Error al hacer la petición:', error);
          },
          complete: () => {
            console.log('Petición completada');
          },
        });
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

  getPopoverContent(item: any): string {
    const content = `Descripcion: ${item.product.description}<br>Categoria: ${item.product.category}`;
    return content;
  }
}
