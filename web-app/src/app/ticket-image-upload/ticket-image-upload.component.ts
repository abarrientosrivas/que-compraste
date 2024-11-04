import { Component, ElementRef, Optional, ViewChild } from '@angular/core';
import { TicketUploadService } from '../ticket-upload.service';
import { CommonModule } from '@angular/common';
import { ActiveToast, Toast, ToastRef, ToastrService } from 'ngx-toastr';
import { HttpEvent, HttpEventType } from '@angular/common/http';
import { ProgressComponent } from './progress/progress.component';

@Component({
  selector: 'app-ticket-image-upload',
  standalone: true,
  imports: [CommonModule, ProgressComponent],
  templateUrl: './ticket-image-upload.component.html',
  styleUrls: ['./ticket-image-upload.component.css'],
})
export class TicketImageUploadComponent {
  selectedFiles: FileList | null = null;
  hasInvalidFiles = false;
  allowedFileTypes = ['image/jpeg', 'image/png', 'application/pdf'];
  percentDone: number = 0;
  postSubscription: any;
  isUploading = false;
  @ViewChild('fileDropRef') fileDropRef: ElementRef | undefined;

  files: any[] = [];
  fileList: FileList | undefined

  /**
   * on file drop handler
   */
  onFileDropped($event: any) {
    this.prepareFilesList($event);
  }

  /**
   * handle file from browsing
   */
  fileBrowseHandler(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      const filesArray = Array.from(input.files);
      this.prepareFilesList(filesArray);
    } else {
      console.error('No files selected');
    }
  }

  /**
   * Convert Files list to normal array list
   * @param files (Files List)
   */
  prepareFilesList(files: Array<any>) {
    for (const item of files) {
      if (!this.allowedFileTypes.includes(item.type))
        this.toastr.warning(
          `Tipo de archivo no valido: ${item.name}`
        );
      item.valid = this.allowedFileTypes.includes(item.type)
      this.files.push(item);
    }

    for (const item of files) {
      if (!item.valid) {
        this.hasInvalidFiles = true
      }
    }
    console.log(this.files)
    //this.uploadFilesSimulator(0);
  }


  /**
   * Delete file from files list
   * @param index (File index)
   */
  deleteFile(index: number) {
    this.files.splice(index, 1);
    this.hasInvalidFiles = false
    for (const item of this.files) {
      if (!item.valid) {
        this.hasInvalidFiles = true
      }
    }
  }

  arrayToFileList(files: File[]): FileList {
    const dataTransfer = new DataTransfer();
    files.forEach(file => dataTransfer.items.add(file));
    return dataTransfer.files;
  }

  /**
   * Simulate the upload process
   */
  /*uploadFilesSimulator(index: number) {
    setTimeout(() => {
      if (index === this.files.length) {
        return;
      } else {
        const progressInterval = setInterval(() => {
          if (this.files[index].progress === 100) {
            clearInterval(progressInterval);
            this.uploadFilesSimulator(index + 1);
          } else {
            this.files[index].progress += 5;
          }
        }, 200);
      }
    }, 1000);*/

   /* this.postSubscription = this.ticketUploadService
      .uploadFile(this.arrayToFileList(index))
      .subscribe({
        next: (event: HttpEvent<any>) => {
          if (event.type === HttpEventType.Response) {
            this.toastr.success('Recibos cargados correctamente');
          } else if (event.type === HttpEventType.UploadProgress) {
            const percentDone = Math.round(
              (100 * (event as any).loaded) / (event as any).total
            );
            this.files[index].progress = percentDone
            //this.updateProgress(percentDone);
          }
        },
        error: (error) => {
          console.error('Error al hacer la petición:', error);
        },
        complete: () => {
          console.log('Petición completada');
          this.isUploading = false;
          this.percentDone = 0;
          this.selectedFiles = null;
          this.files.splice(index, 1);
          if (this.fileInput) {
            this.fileInput.nativeElement.value = '';
          }
          if (index == this.files.length)
            return;
          else if (index < this.files.length) {
            this.uploadFilesSimulator(index + 1)
          }
        },
      });

  }
  */

  /**
   * format bytes
   * @param bytes (File size in bytes)
   * @param decimals (Decimals point)
   */
  formatBytes(bytes: any, decimals = 0) {
    if (bytes === 0) {
      return '0 Bytes';
    }
    const k = 1024;
    const dm = decimals <= 0 ? 0 : decimals || 2;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
  }


  constructor(
    private ticketUploadService: TicketUploadService,
    private toastr: ToastrService
  ) {}

  updateProgress(value: number) {
    this.percentDone = value;
  }

  onCancel() {
    this.percentDone = 0;
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
    /*if (!this.selectedFiles || this.selectedFiles.length === 0) {
      this.toastr.error('Archivos seleccionados invalidos');
      return;
    }*/

    this.isUploading = true;

    this.postSubscription = this.ticketUploadService
      .uploadFile(this.arrayToFileList(this.files))
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
          this.percentDone = 0;
          this.files = [];
          if (this.fileDropRef) {
            this.fileDropRef.nativeElement.value = '';
          }
        },
      });
  }
}
