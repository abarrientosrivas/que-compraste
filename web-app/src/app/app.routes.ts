import { Routes } from '@angular/router';
import { InicioComponent } from './inicio/inicio.component';
import { TicketImageUploadComponent } from './ticket-image-upload/ticket-image-upload.component';

export const routes: Routes = [
  { path: '', component: InicioComponent },
  { path: 'upload', component: TicketImageUploadComponent },
];
