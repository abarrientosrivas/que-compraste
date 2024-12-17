import { Component, OnInit } from '@angular/core';
import { CartsService } from '../../carts.service';
import { Cart, PurchaseItemCart } from '../../carts.service';
import { CommonModule } from '@angular/common';
import { BadgeModule } from 'primeng/badge';
import { NgbPopoverModule, NgbTooltipModule } from '@ng-bootstrap/ng-bootstrap';
import { ImageViewerModule } from 'ngx-image-viewer-3';

@Component({
  selector: 'app-cart-list',
  standalone: true,
  imports: [CommonModule, BadgeModule, NgbPopoverModule, NgbTooltipModule, ImageViewerModule],
  templateUrl: './cart-list.component.html',
  styleUrls: ['./cart-list.component.css'],
})
export class CartListComponent implements OnInit {
  carts: Cart[] = [];
  selectedCart: Cart | null = null;

  constructor(private carritosService: CartsService) {}

  ngOnInit(): void {
    this.loadCarts();
  }

  loadCarts(): void {
    this.carritosService.getCarts().subscribe((carts) => {
      this.carts = carts.map(cart => ({
        ...cart,
        items: cart.items.map((item: any) => ({
          ...item,
          quantity: item.quantity ? Math.round(item.quantity) : item.quantity,
        })),
      }));
      this.selectedCart = this.carts.length > 0 ? this.carts[0] : null;
    });
  }
  
  selectCart(cart: Cart): void {
    this.selectedCart = cart;
  }

  getTotal(item: PurchaseItemCart): number | undefined {
    let total = item.total
    if (!total && item.quantity && item.value) {
      total = item.quantity * item.value
    }
    return total
  } 
  
  formatDate(date: any) {
    const fecha = new Date(date);
    const options: Intl.DateTimeFormatOptions = {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
    };
    return fecha.toLocaleDateString('es-AR', options);
  }

  formatLongDate(date: any): string {
    const fecha = new Date(date);
    const options: Intl.DateTimeFormatOptions = {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    };
    // Use toLocaleDateString with the options
    return fecha.toLocaleDateString('es-ES', options);
  }

  formatCurrency(value: number | undefined): string {
    if (!value) return "";
    return `$${value.toLocaleString('es-AR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    })}`;
  }

  getItemQuantityTotal(cart: Cart): number {
    return cart.items.reduce((total, item) => total + (item.quantity || 0), 0);
  }

  getCartTotal(cart: Cart | null): number {
    if (!cart) return 0;
    return cart.items.reduce((total, item) => total + (this.getTotal(item) || 0), 0);
  }

  downloadCartAsTXT(): void {
    if (!this.selectedCart) return;
  
    const cartLines = [];
    cartLines.push(`Carrito de compra: ${this.formatLongDate(this.selectedCart.date)}`);
    cartLines.push(`Total tentativo: ${this.formatCurrency(this.getCartTotal(this.selectedCart))}\n`);
  
    this.selectedCart.items.forEach((item, index) => {
      cartLines.push(
        `${index + 1}. Producto: ${item.product?.title || item.read_product_text || item.read_product_key || 'Unknown Product'}\n` +
        `   Cantidad: ${item.quantity}\n` +
        `   Precio Unitario: ${item.value ? this.formatCurrency(item.value) : 'N/A'}\n` +
        `   Total: ${this.formatCurrency(this.getTotal(item))}`
      );
    });
  
    const textContent = cartLines.join('\n');
  
    const blob = new Blob([textContent], { type: 'text/plain' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const formattedCartDate = new Date(this.selectedCart.date)
      .toISOString()
      .split('T')[0];

    a.download = `carrito_${formattedCartDate}.txt`;
    a.click();
  
    window.URL.revokeObjectURL(url);
  }

  downloadCartAsCSV(): void {
    if (!this.selectedCart) return;
  
    const rows: string[] = [];
  
    rows.push('"Fecha";"Total tentativo";"Producto";"Cantidad";"Precio unitario";"Total de ítem"');
  
    this.selectedCart.items.forEach((item) => {
      const date = this.formatLongDate(this.selectedCart?.date);
      const totalTentativo = this.formatCurrency(this.getCartTotal(this.selectedCart));
      const product = item.product?.title || item.read_product_text || 'Unknown Product';
      const quantity = item.quantity || 0;
      const priceUnit = item.value ? this.formatCurrency(item.value).replace('$', '') : '0.00';
      const itemTotal = this.formatCurrency(this.getTotal(item)).replace('$', '');
  
      rows.push(
        `"${date}";"${totalTentativo}";"${product}";${quantity};${priceUnit};${itemTotal}`
      );
    });
  
    const csvContent = rows.join('\n');
  
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = window.URL.createObjectURL(blob);
  
    const a = document.createElement('a');
    a.href = url;
    const formattedCartDate = new Date(this.selectedCart.date)
      .toISOString()
      .split('T')[0];

    a.download = `carrito_${formattedCartDate}.csv`;
    a.click();
  
    window.URL.revokeObjectURL(url);
  }  
}