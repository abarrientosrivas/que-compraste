import { Routes } from '@angular/router';
import { InicioComponent } from './inicio/inicio.component';
import { TicketImageUploadComponent } from './ticket-image-upload/ticket-image-upload.component';
import { ReportesComponent } from './reportes/reportes.component';
import { CompraComponent } from './purchases/purchase/compra.component';
import { PurchaseListComponent } from './purchases/purchase-list/purchase-list.component';

export const routes: Routes = [
  { path: '', component: InicioComponent },
  { path: 'carga', component: TicketImageUploadComponent },
  { path: 'reportes', component: ReportesComponent },
  { path: 'compras/:compraId', component: CompraComponent },
  { path: 'compras', component: PurchaseListComponent },
];
