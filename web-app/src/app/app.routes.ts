import { Routes } from '@angular/router';
import { InicioComponent } from './inicio/inicio.component';
import { TicketImageUploadComponent } from './ticket-image-upload/ticket-image-upload.component';
import { ReportesComponent } from './reportes/reportes.component';
import { CompraComponent } from './purchases/purchase/compra.component';
import { PurchaseListComponent } from './purchases/purchase-list/purchase-list.component';
import { PurchaseFormComponent } from './purchases/purchase-form/purchase-form.component';
import { PredictionComponent } from './prediction/prediction/prediction.component';
import { CartListComponent } from './carts/cart-list/cart-list.component';

export const routes: Routes = [
  { path: '', redirectTo: '/carga', pathMatch: 'full' },
  { path: 'carga', component: TicketImageUploadComponent },
  { path: 'reportes', component: ReportesComponent },
  { path: 'predicciones', component: PredictionComponent },
  { path: 'carros-de-compra', component: CartListComponent },
  { path: 'compras/:compraId', component: CompraComponent },
  { path: 'compras/:compraId/edit', component: PurchaseFormComponent },
  { path: 'compras', component: PurchaseListComponent },
  { path: '**', component: InicioComponent },
];
