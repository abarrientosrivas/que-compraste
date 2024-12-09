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

  getCartTotal(cart: Cart): number {
    return cart.items.reduce((total, item) => total + (this.getTotal(item) || 0), 0);
  }
}
