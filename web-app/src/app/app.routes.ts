import { Routes } from '@angular/router';
import { InicioComponent } from './inicio/inicio.component';
import { TicketImageUploadComponent } from './ticket-image-upload/ticket-image-upload.component';
import { ReportesComponent } from './reportes/reportes.component';
import { VerCompraComponent } from './ver-compra/ver-compra.component';

export const routes: Routes = [
  { path: '', component: InicioComponent },
  { path: 'upload', component: TicketImageUploadComponent },
  { path: 'reportes', component: ReportesComponent },
  { path: 'compras/:compraId', component: VerCompraComponent },
];
