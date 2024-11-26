import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { TicketUploadService } from '../ticket-upload.service';
import { CommonModule } from '@angular/common';
import { ToastrService } from 'ngx-toastr';
import { HttpEvent, HttpEventType } from '@angular/common/http';
import { ProgressComponent } from './progress/progress.component';
import { ComprasService } from '../purchases/shared/compras.service';
import { ChangeDetectorRef } from '@angular/core';
import { NgZone } from '@angular/core';

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
  receiptList: any[] = [];
  selectedReceipt: any;

  trackedReceiptIds: number[] = [];
  files: any[] = [];
  fileList: FileList | undefined;

  constructor(
    private ticketUploadService: TicketUploadService,
    private toastr: ToastrService,
    private comprasService: ComprasService,
    private cdr: ChangeDetectorRef,
    private zone: NgZone
  ) {}

  ngOnInit(): void {
    this.trackedReceiptIds = JSON.parse(
      localStorage.getItem('trackedReceiptIds') || '[]'
    );
    this.loadReceipts().then(() => {
      // Start SSE subscriptions after receipts have been loaded
      this.sseStatusChange();
    });
  }

  onSelectedReceipt(receipt: any) {
    this.selectedReceipt = receipt;
  }

  async loadReceipts() {
    if (this.trackedReceiptIds.length > 0) {
      this.receiptList = [];
      const receiptPromises = this.trackedReceiptIds.map((receiptId) =>
        this.fetchReceipt(receiptId)
      );
      await Promise.all(receiptPromises);
      // Sort the receiptList after all receipts have been loaded
      this.receiptList.sort(
        (a: any, b: any) =>
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );
    }
  }

  async fetchReceipt(receiptId: number) {
    try {
      const receipt = await this.ticketUploadService.getReceipt(receiptId).toPromise();

      try {
        const blob = await this.comprasService.getReceiptImage(receipt.image_url).toPromise();
    
        if (blob) {
          receipt.image_url = URL.createObjectURL(blob);
        } else {
          console.warn(`No image returned for receipt ID: ${receiptId}`);
          receipt.image_url = ''; // Provide a fallback or placeholder if needed
        }
      } catch (error) {
        console.error('Error fetching image for receipt:', error);
      }
  
      this.receiptList.push(receipt);
    } catch (error) {
      console.error('Error fetching receipt:', error);
    }
  }

  sseStatusChange() {
    for (let receiptId of this.trackedReceiptIds) {
      this.ticketUploadService.getStatusUpdates(receiptId).subscribe({
        next: (event) => {
          console.log('Status change from id: ', event);

          this.ticketUploadService.getReceipt(event).subscribe({
            next: (receipt) => {
              this.zone.run(() => {
                let index = this.receiptList.findIndex(
                  (item: { id: any }) => item.id === receipt.id
                );

                if (index !== -1) {
                  this.receiptList[index] = {
                    ...this.receiptList[index],
                    status: receipt.status,
                  };
                } else {
                  // If the receipt is not found, add it to receiptList
                  this.addReceiptToList(receipt);
                }
              });
            },
            error: (error) => {
              console.error('Error fetching receipt:', error);
            },
          });
        },
      });
    }
  }

  sseStatusChangeReceipt(receiptId: number) {
    this.ticketUploadService.getStatusUpdates(receiptId).subscribe({
      next: (event) => {
        console.log('Status change from id: ', event);

        this.ticketUploadService.getReceipt(event).subscribe({
          next: (receipt) => {
            this.zone.run(() => {
              let index = this.receiptList.findIndex(
                (item: { id: number }) => item.id === receipt.id
              );

              if (index !== -1) {
                this.receiptList[index] = {
                  ...this.receiptList[index],
                  status: receipt.status,
                };
              } else {
                // If the receipt is not found, add it to receiptList
                this.addReceiptToList(receipt);
              }
            });
          },
          error: (error) => {
            console.error('Error fetching receipt:', error);
          },
        });
      },
    });
  }

  addReceiptToList(receipt: any) {
  // Fetch the receipt image
  this.comprasService.getReceiptImage(receipt.image_url).subscribe({
    next: (blob: Blob | undefined) => {
      if (blob) {
        receipt.image_url = URL.createObjectURL(blob); // Only create object URL if blob is defined
        // Add the receipt to the receiptList
        this.receiptList.push(receipt);
        // Sort the receiptList
        this.receiptList.sort(
          (a: any, b: any) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        // Trigger change detection
        this.cdr.detectChanges();
      } else {
        console.error('Blob is undefined for receipt:', receipt);
      }
    },
    error: (error) => {
      console.error('Error fetching receipt image:', error);
    },
  });
}

  onFileDropped($event: any) {
    this.prepareFilesList($event);
  }

  fileBrowseHandler(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      const filesArray = Array.from(input.files);
      this.prepareFilesList(filesArray);
    } else {
      console.error('No files selected');
    }
  }

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

  onSubmit() {
    if (this.files.length === 0) {
      this.toastr.error('No files to upload');
      return;
    }

    this.isUploading = true;

    this.postSubscription = this.ticketUploadService
      .uploadFile(this.arrayToFileList(this.files))
      .subscribe({
        next: (event: HttpEvent<any>) => {
          if (event.type === HttpEventType.Response) {
            this.toastr.success('Recibos cargados correctamente');

            if (localStorage.getItem('trackedReceiptIds')) {
              this.trackedReceiptIds = JSON.parse(
                localStorage.getItem('trackedReceiptIds')!
              );
            } else {
              localStorage.setItem('trackedReceiptIds', JSON.stringify([]));
              this.trackedReceiptIds = [];
            }

            event.body.forEach((receipt: any) => {
              this.trackedReceiptIds.push(receipt.id);
              // Immediately add the receipt to receiptList
              this.addReceiptToList(receipt);
              // Start SSE subscription for this receipt
              this.sseStatusChangeReceipt(receipt.id);
            });
            console.log(this.trackedReceiptIds);

            localStorage.setItem(
              'trackedReceiptIds',
              JSON.stringify(this.trackedReceiptIds)
            );

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
          this.isUploading = false;
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

  acknowledgeReceipt(receiptId: number) {
    // Remove the receipt ID from trackedReceiptIds
    this.trackedReceiptIds = this.trackedReceiptIds.filter((id) => id !== receiptId);
    localStorage.setItem('trackedReceiptIds', JSON.stringify(this.trackedReceiptIds));
  
    // Remove the receipt from receiptList
    this.receiptList = this.receiptList.filter((receipt: any) => receipt.id !== receiptId);
  
    console.log(`Receipt with ID ${receiptId} acknowledged and removed.`);
  }  
}
