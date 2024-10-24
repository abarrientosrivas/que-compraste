import { Component, inject, OnInit, ViewChild } from '@angular/core';
import { ReactiveFormsModule, FormBuilder, FormArray, Validators } from '@angular/forms';
import { ComprasService } from '../shared/compras.service';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { ProductSearchComponent } from '../../product-search/product-search.component';

@Component({
  selector: 'app-purchase-form',
  standalone: true,
  imports: [ReactiveFormsModule, CommonModule, ProductSearchComponent, RouterLink],
  templateUrl: './purchase-form.component.html',
  styleUrl: './purchase-form.component.css',
})
export class PurchaseFormComponent implements OnInit {

  purchaseForm: any;
  itemToChange: any;
  replacementItem: any;
  errorMessage: any;
  @ViewChild(ProductSearchComponent) productSearchComponent!: ProductSearchComponent;
  noResults: any;
  productCode: any;


  constructor(
    private formBuilder: FormBuilder,
    private router: Router,
    private comprasService: ComprasService
  ) {
    this.purchaseForm = this.formBuilder.group({
      date: ['', Validators.required],
      discount: [''],
      subtotal: [''],
      total: ['', Validators.required],
      tips: [''],
      read_entity_address: [''],
      read_entity_name: [''],
      read_entity_location: [''],
      items: this.formBuilder.array([]),
    });
  }

  private activatedRoute = inject(ActivatedRoute);
  compraId = this.activatedRoute.snapshot.params['compraId'];

  ngOnInit(): void {
    this.comprasService.getCompraById(this.compraId).subscribe({
      next: (data: any) => {
        this.setFormValues(data)
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

  setFormValues(data: any): void {
    this.purchaseForm.patchValue({
      read_entity_name: data.read_entity_name,
      read_entity_location: data.read_entity_location,
      read_entity_address: data.read_entity_address,
      read_entity_identification: data.read_entity_identification,
      date: data.date,
      subtotal: data.subtotal,
      discount: data.discount,
      tips: data.tips,
      total: data.total
    })
    const itemsArray = this.formBuilder.array(
      data.items
      .sort((a: any, b: any) => a.id - b.id) // Order items by id
      .map((item: any) => this.formBuilder.group({
        read_product_key: [item.read_product_key],
        read_product_text: [item.read_product_text],
        quantity: [item.quantity],
        value: [item.value],
        total: [item.total],
        product_id: [item.product_id],
        id: [item.id]
      }))
    );
    this.purchaseForm.setControl('items', itemsArray);
  }

  get items() {
    return this.purchaseForm.get('items') as FormArray;
  }

  removeItem(index: number): void {
    const control = <FormArray>this.purchaseForm.controls['items'];
    control.removeAt(index);
  }

  seleccionarItem(item: any) {
    console.log(item.value)
    this.itemToChange = item.value;
  }

  onProductSelected(event: any) {
    this.replacementItem = event
    console.log(event)
  }

  resetProductSearchForm() {
    this.productSearchComponent.resetForm();
  }

  changeItem() {
    const itemsArray = this.purchaseForm.get('items') as FormArray;
    const index = itemsArray.controls.findIndex(control => control.value === this.itemToChange);
    if (index !== -1) {
      this.noResults = false;
      itemsArray.at(index).patchValue({
        read_product_key: this.replacementItem.code,
        read_product_text: this.replacementItem.product.title,
        product_id: this.replacementItem.product_id
      });
    }
    this.resetProductSearchForm()
    this.replacementItem = null
  }

  cancel() {
    this.resetProductSearchForm()
    this.replacementItem = null
  }

  onSubmit() {

    this.comprasService.updatePurchase(this.compraId, this.purchaseForm.value).subscribe({
      next: (data) => {
        console.log('Respuesta del servidor:', data);
      },
      error: (error) => {
        console.error('Error al hacer la petición:', error);
        this.errorMessage = true
      },
      complete: () => {
        console.log('Petición completada');
        this.errorMessage = false
        this.router.navigate(['/compras', this.compraId]);
      },
    });

  }

  onNoResults(event: any) {
    this.noResults = event;
  }

  createProductCode() {

    const itemsArray = this.purchaseForm.get('items') as FormArray;
    const index = itemsArray.controls.findIndex(control => control.value === this.itemToChange);
    if (index !== -1) {
      this.itemToChange.read_product_key = this.productCode
      this.itemToChange.product_id = null
    }
    this.resetProductSearchForm()
    console.log(this.itemToChange)
    /*this.comprasService.updateProductCode(this.compraId, this.itemToChange.id, this.productCode).subscribe({
      next: (data) => {
        console.log('Product code created:', data);
      },
      error: (error) => {
        console.error('Error creating product code:', error);
      }
    });*/
  }

  onProductCode(query: any) {
    this.productCode = query.toString()
  }

}
