import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { TicketUploadService } from '../ticket-upload.service';
import { CommonModule } from '@angular/common';
import { ToastrService } from 'ngx-toastr';
import { HttpEvent, HttpEventType } from '@angular/common/http';
import { ProgressComponent } from './progress/progress.component';
import { ComprasService } from '../purchases/shared/compras.service';

@Component({
  selector: 'app-ticket-image-upload',
  standalone: true,
  imports: [CommonModule, ProgressComponent],
  templateUrl: './ticket-image-upload.component.html',
  styleUrls: ['./ticket-image-upload.component.css'],
})
export class TicketImageUploadComponent implements OnInit {
  selectedFiles: FileList | null = null;
  hasInvalidFiles = false;
  allowedFileTypes = ['image/jpeg', 'image/png', 'application/pdf'];
  percentDone: number = 0;
  postSubscription: any;
  isUploading = false;
  @ViewChild('fileDropRef') fileDropRef: ElementRef | undefined;
  receiptList: any;
  selectedReceipt: any;

  files: any[] = [];
  fileList: FileList | undefined;

  constructor(
    private ticketUploadService: TicketUploadService,
    private toastr: ToastrService,
    private comprasService: ComprasService
  ) {}

  onSelectedReceipt(receipt: any) {
    this.selectedReceipt = receipt;
  }

  ngOnInit(): void {
    this.ticketUploadService.getStatusUpdates(133).subscribe({
      next: (event) => {
        console.log(event);
      },
    });
    this.loadReceipts();
  }

  loadReceipts() {
    if (localStorage.getItem('uploadedFiles')) {
      this.receiptList = JSON.parse(localStorage.getItem('uploadedFiles')!);
      for (let receipt of this.receiptList) {
        this.comprasService.getReceiptImage(receipt.image_url).subscribe({
          next: (blob: Blob) => {
            receipt.image_url = URL.createObjectURL(blob);
          },
          error: (error) => {
            console.error('Error al hacer la petición:', error);
          },
        });
      }
    }
  }

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
        this.toastr.warning(`Tipo de archivo no valido: ${item.name}`);
      item.valid = this.allowedFileTypes.includes(item.type);
      this.files.push(item);
    }

    for (const item of files) {
      if (!item.valid) {
        this.hasInvalidFiles = true;
      }
    }
    console.log(this.files);
    //this.uploadFilesSimulator(0);
  }

  deleteFile(index: number) {
    this.files.splice(index, 1);
    this.hasInvalidFiles = false;
    for (const item of this.files) {
      if (!item.valid) {
        this.hasInvalidFiles = true;
      }
    }
  }

  arrayToFileList(files: File[]): FileList {
    const dataTransfer = new DataTransfer();
    files.forEach((file) => dataTransfer.items.add(file));
    return dataTransfer.files;
  }

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
            let localStorageData = null;
            if (localStorage.getItem('uploadedFiles')) {
              localStorageData = JSON.parse(
                localStorage.getItem('uploadedFiles')!
              );
            } else {
              localStorage.setItem('uploadedFiles', JSON.stringify([]));
              localStorageData = JSON.parse(
                localStorage.getItem('uploadedFiles')!
              );
            }
            event.body.forEach((receipt: any) => {
              localStorageData.push({
                id: receipt.id,
                status: receipt.status,
                reference_name: receipt.reference_name,
                image_url: receipt.image_url,
              });
            });
            console.log(localStorageData);

            localStorage.setItem(
              'uploadedFiles',
              JSON.stringify(localStorageData)
            );
            this.loadReceipts();

            console.log('Respuesta del servidor: ', event.body);
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
