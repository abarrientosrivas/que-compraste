import { Component, ElementRef, ViewChild } from '@angular/core';
import { TicketUploadService } from '../ticket-upload.service';
import { CommonModule } from '@angular/common';
import { ActiveToast, Toast, ToastRef, ToastrService } from 'ngx-toastr';
import { HttpEvent, HttpEventType } from '@angular/common/http';

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
  percentDone: number | null = null;
  postSubscription: any;
  isUploading = false;
  @ViewChild('fileInput') fileInput: ElementRef | undefined;

  constructor(
    private ticketUploadService: TicketUploadService,
    private toastr: ToastrService
  ) {}

  updateProgress(value: number) {
    this.percentDone = value;
  }

  onCancel() {
    this.percentDone = null;
    this.postSubscription.unsubscribe();
    this.isUploading = false;
  }

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

    this.isUploading = true;

    this.postSubscription = this.ticketUploadService
      .uploadFile(this.selectedFiles)
      .subscribe({
        next: (event: HttpEvent<any>) => {
          if (event.type === HttpEventType.Response) {
            this.toastr.success('Recibos cargados correctamente');
          } else if (event.type === HttpEventType.UploadProgress) {
            const percentDone = Math.round(
              (100 * (event as any).loaded) / (event as any).total
            );
            this.updateProgress(percentDone);
          }
        },
        error: (error) => {
          console.error('Error al hacer la petición:', error);
        },
        complete: () => {
          console.log('Petición completada');
          this.isUploading = false;
          this.percentDone = null;
          this.selectedFiles = null;
          if (this.fileInput) {
            this.fileInput.nativeElement.value = '';
          }
        },
      });
  }
}
