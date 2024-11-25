import { Component, OnInit } from '@angular/core';
import { ProductsService } from '../../products.service';
import { DropdownModule } from 'primeng/dropdown';
import { ReactiveFormsModule, FormGroup, FormControl } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { formatDate } from '@angular/common';

import Chart from 'chart.js/auto';

@Component({
  selector: 'app-prediction',
  standalone: true,
  imports: [DropdownModule, ReactiveFormsModule, CommonModule],
  templateUrl: './prediction.component.html',
  styleUrl: './prediction.component.css',
})
export class PredictionComponent implements OnInit {
  products: any[] | undefined;
  selectedProduct: any;
  historicPointsCount: number = 0;
  formGroup: FormGroup<any> = new FormGroup({});
  myChart: any;
  ctx = document.getElementById('ctx');
  predictionExist = false;
  mainPrediction: any;

  options: any;
  data1: any = {
    labels: [],
    datasets: [
      {
        data: [],
      },
    ],
  };

  constructor(private productsService: ProductsService) {}

  prediction = (ctx: any, value: any) => {
    if (ctx.p0.$context.dataIndex + 1 > this.historicPointsCount) {
      return value;
    }
    return undefined;
  };

  ngOnInit(): void {
    this.formGroup = new FormGroup({
      selectedProduct: new FormControl<object | null>(null),
    });

    this.formGroup.get('selectedProduct')?.valueChanges.subscribe((item) => {
      this.predictionExist = false;
      this.mainPrediction = null;
      console.log(item);
      if (this.myChart) {
        this.myChart.destroy();
      }
      this.selectedProduct = item;
      this.productsService
        .getHistoricByProductCode(item.read_product_key)
        .subscribe({
          next: (data) => {
            console.log('Historic: ', data);
            this.historicPointsCount = data.length;
            if (data.length != 1) {
              data = data.sort(
                (a: any, b: any) =>
                  new Date(a.date).getTime() - new Date(b.date).getTime()
              );
            }
            if (data.length == 1) {
              this.data1.labels = [
                formatDate(data[0].date, 'dd-MM-yyyy', 'en-US'),
                formatDate(data[0].date, 'dd-MM-yyyy', 'en-US'),
              ];
              this.data1.datasets[0].data = [
                data[0].quantity,
                data[0].quantity,
              ];
            } else {
              this.data1.labels = data.map((element) => {
                return formatDate(element.date, 'dd-MM-yyyy', 'en-US');
              });
              this.data1.datasets[0].data = data.map((element) => {
                return element.quantity;
              });
            }
          },
          error: (error) => {
            console.error('Error al hacer la petición: ', error);
          },
          complete: () => {
            console.log('Petición completada');

            this.productsService
              .getLastPredictionByProductCode(item.read_product_key)
              .subscribe({
                next: (data) => {
                  console.log('Last predictions: ', data);
                  let items = data.items;
                  if (items.length != 1) {
                    items = items.sort(
                      (a: any, b: any) =>
                        new Date(a.date).getTime() - new Date(b.date).getTime()
                    );
                  }

                  // Filter items to include only those with a future date
                  items = items.filter((element: any) => {
                    return new Date(element.date).getTime() > new Date().getTime();
                  });

                  console.log('Items: ', items);

                  const today = new Date().getTime();

                  // Find the closest future item
                  this.mainPrediction = items.reduce((closest: any, current: any) => {
                    const currentDiff = new Date(current.date).getTime() - today;
                    const closestDiff = new Date(closest.date).getTime() - today;

                    // Ensure we're only considering future dates, and find the smallest difference
                    if (currentDiff >= 0 && (closestDiff < 0 || currentDiff < closestDiff)) {
                      return {
                        ...current,
                        quantity: Math.round(current.quantity), // Round the quantity of the current item
                      };
                    }

                    return {
                      ...closest,
                      quantity: Math.round(closest.quantity), // Round the quantity of the closest item
                    };
                  }, {
                    ...items[0],
                    quantity: Math.round(items[0].quantity), // Initialize with a rounded first item
                  });
                  this.predictionExist = true;

                  this.data1.labels = [
                    ...this.data1.labels,
                    ...items.map((element: any) => {
                      return formatDate(element.date, 'dd-MM-yyyy', 'en-US');
                    }),
                  ];
                  this.data1.datasets[0].data = [
                    ...this.data1.datasets[0].data,
                    ...items.map((element: any) => {
                      return Math.round(element.quantity);
                    }),
                  ];
                  console.log(
                    'Labels: ',
                    this.data1.labels,
                    'data: ',
                    this.data1.datasets[0].data
                  );
                },
                error: (error) => {
                  console.error('Error al hacer la petición: ', error);
                  this.renderLineChart();
                },
                complete: () => {
                  console.log('Petición completada');
                  this.data1.datasets[0].label = '';
                  this.renderLineChart();
                },
              });
          },
        });
    });

    this.productsService.getProductCodes().subscribe({
      next: (data) => {
        this.products = data;
        console.log(data);
      },
    });
  }

  renderLineChart() {
    if (this.myChart) {
      this.myChart.destroy();
    }
    this.myChart = new Chart('ctx', {
      type: 'line',
      data: {
        labels: this.data1.labels,
        datasets: [
          {
            label: '',
            data: this.data1.datasets[0].data,
            fill: false,
            borderColor: 'rgb(75, 192, 192)',
            tension: 0.1,
            segment: {
              borderColor: (ctx) => this.prediction(ctx, 'rgb(192,75,75)'),
            },
            spanGaps: true,
          },
        ],
      },
      options: {
        maintainAspectRatio: false,
        aspectRatio: 0.6,
        plugins: {
          legend: {
            display: false,
            labels: {
              color: 'black',
            },
          },
        },
        scales: {
          x: {
            ticks: {
              color: 'black',
            },
            grid: {
              color: '#DAD8C9',
            },
          },
          y: {
            ticks: {
              color: 'black',
            },
            grid: {
              color: '#DAD8C9',
            },
          },
        },
      },
    });
  }
}
