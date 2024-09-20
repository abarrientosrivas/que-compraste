import { Component } from '@angular/core';
import { TicketUploadService } from '../ticket-upload.service';

@Component({
  selector: 'app-ticket-image-upload',
  standalone: true,
  imports: [],
  templateUrl: './ticket-image-upload.component.html',
  styleUrl: './ticket-image-upload.component.css',
})
export class TicketImageUploadComponent {
  selectedFile: File | null = null;

  constructor(private ticketUploadService: TicketUploadService) {}

  onFileSelected(event: any) {
    this.selectedFile = event.target.files[0];
  }

  onSubmit() {
    if (!this.selectedFile) {
      console.error('No file selected');
      return;
    }

    this.ticketUploadService.uploadFile(this.selectedFile).subscribe({
      next: (data) => {
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
}
