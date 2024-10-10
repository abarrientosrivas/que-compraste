import { Component } from '@angular/core';
import { TicketUploadService } from '../ticket-upload.service';
import { CommonModule } from '@angular/common';
import { ToastrService } from 'ngx-toastr';

@Component({
  selector: 'app-ticket-image-upload',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './ticket-image-upload.component.html',
  styleUrl: './ticket-image-upload.component.css',
})
export class TicketImageUploadComponent {
  selectedFiles: FileList | null = null;
  hasInvalidFiles = false;
  allowedFileTypes = ['image/jpeg', 'image/png', 'application/pdf'];

  constructor(
    private ticketUploadService: TicketUploadService,
    private toastr: ToastrService
  ) {}

  get selectedFilesNames() {
    if (!this.selectedFiles) return [];
    return Array.from(this.selectedFiles).map((file) => ({
      name: file.name,
      isValid: this.allowedFileTypes.includes(file.type),
    }));
  }

  onFilesSelected(event: any) {
    this.selectedFiles = event.target.files;
    this.hasInvalidFiles = false;

    if (this.selectedFiles) {
      for (let i = 0; i < this.selectedFiles.length; i++) {
        if (!this.allowedFileTypes.includes(this.selectedFiles[i].type)) {
          this.toastr.warning(
            `Tipo de archivo no valido: ${this.selectedFiles[i].name}`
          );
          this.hasInvalidFiles = true;
        }
      }
    }
  }

  onSubmit() {
    if (!this.selectedFiles || this.selectedFiles.length === 0) {
      this.toastr.error('Archivos seleccionados invalidos');
      return;
    }

    this.ticketUploadService.uploadFile(this.selectedFiles).subscribe({
      next: (data) => {
        this.toastr.success('Archivos subidos correctamente');
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
