import { Component, OnInit } from '@angular/core';
import { ProductsService } from '../../products.service';
import { CategoriesService } from '../../categories.service';
import { DropdownModule } from 'primeng/dropdown';
import { ReactiveFormsModule, FormGroup, FormControl } from '@angular/forms';
import { CommonModule, formatDate } from '@angular/common';
import { forkJoin } from 'rxjs';
import { switchMap } from 'rxjs/operators';
import { BadgeModule } from 'primeng/badge';
import Chart from 'chart.js/auto';

@Component({
  selector: 'app-prediction',
  standalone: true,
  imports: [DropdownModule, ReactiveFormsModule, CommonModule, BadgeModule],
  templateUrl: './prediction.component.html',
  styleUrl: './prediction.component.css',
})
export class PredictionComponent implements OnInit {
  products: any[] | undefined;
  categories: any[] | undefined;
  selectedProduct: any;
  selectedCategory: any;
  // Removed historicPointsCount, now using lastHistoricDate
  lastHistoricDate: Date | null = null;

  formGroup: FormGroup<any> = new FormGroup({});
  myChart: any;
  predictionExist = false;
  mainPrediction: any;

  originalData: { date: string | Date; quantity: number }[] = [];

  data1: any = {
    labels: [],
    datasets: [
      {
        data: [],
      },
    ],
  };

  constructor(
    private productsService: ProductsService,
    private categoriesService: CategoriesService
  ) {}

  prediction = (ctx: any, value: any) => {
    if (!this.lastHistoricDate) return undefined;

    const dataIndex = ctx.p0.$context.dataIndex;
    const currentLabel = this.data1.labels[dataIndex]; 
    const currentDate = new Date(currentLabel.split('-').reverse().join('-')); 
    if (currentDate.getTime() >= this.lastHistoricDate.getTime()) {
      return value;
    }

    return undefined; 
  };

  ngOnInit(): void {
    this.formGroup = new FormGroup({
      selectedProduct: new FormControl<object | null>(null),
      selectedCategory: new FormControl<object | null>(null),
      startDate: new FormControl<string | null>(null),
      endDate: new FormControl<string | null>(null),
    });

    this.formGroup.get('startDate')?.valueChanges.subscribe((startDateVal) => {
      const endDateVal = this.formGroup.get('endDate')?.value;
      if (startDateVal && endDateVal && new Date(startDateVal) > new Date(endDateVal)) {
        this.formGroup.get('endDate')?.setValue(startDateVal);
      }
      this.filterChartData();
    });
    this.formGroup.get('endDate')?.valueChanges.subscribe((endDateVal) => {
      const startDateVal = this.formGroup.get('startDate')?.value;
      if (startDateVal && endDateVal && new Date(endDateVal) < new Date(startDateVal)) {
        this.formGroup.get('startDate')?.setValue(endDateVal);
      }
      this.filterChartData();
    });

    this.formGroup.get('selectedProduct')?.valueChanges.subscribe((item) => {
      this.predictionExist = false;
      this.mainPrediction = null;
      
      this.formGroup.get('startDate')?.reset(null);
      this.formGroup.get('endDate')?.reset(null);

      if (this.myChart) {
        this.myChart.destroy();
      }

      this.formGroup.get('selectedCategory')?.setValue(null, { emitEvent: false });
      this.selectedCategory = null;
      this.selectedProduct = item;

      this.productsService.getHistoricByProductCode(item.read_product_key).subscribe({
        next: (data) => {
          if (data.length > 1) {
            data = data.sort(
              (a: any, b: any) =>
                new Date(a.date).getTime() - new Date(b.date).getTime()
            );
          }

          this.originalData = data.map((d: any) => ({ date: d.date, quantity: d.quantity }));

          if (data.length > 1) {
            this.lastHistoricDate = new Date(data[data.length - 2].date);
          } else if (data.length === 1) {
            this.lastHistoricDate = new Date(data[0].date);
          } else {
            this.lastHistoricDate = null;
          }
        },
        error: (error) => {
          console.error('Error al hacer la petición: ', error);
        },
        complete: () => {
          this.productsService.getLastPredictionByProductCode(item.read_product_key).subscribe({
            next: (data) => {
              let items = data.items;
              if (items.length !== 1) {
                items = items.sort(
                  (a: any, b: any) =>
                    new Date(a.date).getTime() - new Date(b.date).getTime()
                );
              }

              items = items.filter((element: any) => {
                return new Date(element.date).getTime() > new Date().getTime();
              });

              const today = new Date().getTime();

              this.mainPrediction = items.reduce(
                (closest: any, current: any) => {
                  const currentDiff = new Date(current.date).getTime() - today;
                  const closestDiff = new Date(closest.date).getTime() - today;

                  if (currentDiff >= 0 && (closestDiff < 0 || currentDiff < closestDiff)) {
                    return { ...current, quantity: Math.round(current.quantity) };
                  }

                  return { ...closest, quantity: Math.round(closest.quantity) };
                },
                { ...items[0], quantity: Math.round(items[0].quantity) }
              );

              this.predictionExist = true;

              const predictionData = items.map((element: any) => ({
                date: element.date,
                quantity: Math.round(element.quantity),
              }));
              this.originalData = [...this.originalData, ...predictionData];
            },
            error: (error) => {
              console.error('Error al hacer la petición: ', error);
              this.filterChartData();
            },
            complete: () => {
              this.filterChartData();
            },
          });
        },
      });
    });

    this.formGroup.get('selectedCategory')?.valueChanges.subscribe((item) => {
      this.predictionExist = false;
      this.mainPrediction = null;
      
      this.formGroup.get('startDate')?.reset(null);
      this.formGroup.get('endDate')?.reset(null);

      if (this.myChart) {
        this.myChart.destroy();
      }

      this.formGroup.get('selectedProduct')?.setValue(null, { emitEvent: false });
      this.selectedProduct = null;
      this.selectedCategory = item;

      this.categoriesService.getHistoricByCategoryCode(item.code).subscribe({
        next: (data) => {
          if (data.length !== 1) {
            data = data.sort(
              (a: any, b: any) =>
                new Date(a.date).getTime() - new Date(b.date).getTime()
            );
          }

          this.originalData = data.map((d: any) => ({ date: d.date, quantity: d.quantity }));

          if (data.length > 1) {
            this.lastHistoricDate = new Date(data[data.length - 2].date);
          } else if (data.length === 1) {
            this.lastHistoricDate = new Date(data[0].date);
          } else {
            this.lastHistoricDate = null;
          }
        },
        error: (error) => {
          console.error('Error al hacer la petición: ', error);
        },
        complete: () => {
          this.categoriesService.getLastPredictionByCategoryCode(item.code).subscribe({
            next: (data) => {
              let items = data.items;
              if (items.length !== 1) {
                items = items.sort(
                  (a: any, b: any) =>
                    new Date(a.date).getTime() - new Date(b.date).getTime()
                );
              }

              items = items.filter((element: any) => {
                return new Date(element.date).getTime() > new Date().getTime();
              });

              const today = new Date().getTime();

              this.mainPrediction = items.reduce(
                (closest: any, current: any) => {
                  const currentDiff = new Date(current.date).getTime() - today;
                  const closestDiff = new Date(closest.date).getTime() - today;

                  if (currentDiff >= 0 && (closestDiff < 0 || currentDiff < closestDiff)) {
                    return { ...current, quantity: Math.round(current.quantity) };
                  }

                  return { ...closest, quantity: Math.round(closest.quantity) };
                },
                { ...items[0], quantity: Math.round(items[0].quantity) }
              );

              this.predictionExist = true;
              const predictionData = items.map((element: any) => ({
                date: element.date,
                quantity: Math.round(element.quantity),
              }));
              this.originalData = [...this.originalData, ...predictionData];
            },
            error: (error) => {
              console.error('Error al hacer la petición: ', error);
              this.filterChartData();
            },
            complete: () => {
              this.filterChartData();
            },
          });
        },
      });
    });

    this.categoriesService
      .getCategoryCodes()
      .pipe(
        switchMap((codes: string[]) => {
          const categoryObservables = codes.map((code) =>
            this.categoriesService.getCategories(code)
          );
          return forkJoin(categoryObservables);
        })
      )
      .subscribe({
        next: (categoriesArray) => {
          this.categories = categoriesArray
            .flat()
            .sort((a: any, b: any) =>
              (a.name_es_es || '').localeCompare(b.name_es_es || '')
            );
        },
        error: (err) => {
          console.error('Error fetching categories:', err);
        },
      });

    this.productsService.getProductCodes().subscribe({
      next: (data) => {
        this.products = data.sort((a: any, b: any) =>
          (a.read_product_text || '').localeCompare(b.read_product_text || '')
        );
      },
    });
  }

  filterChartData() {
    const startDateVal = this.formGroup.get('startDate')?.value;
    const endDateVal = this.formGroup.get('endDate')?.value;

    let filteredData = [...this.originalData];

    if (startDateVal) {
      const start = new Date(startDateVal);
      filteredData = filteredData.filter((d) => new Date(d.date) >= start);
    }

    if (endDateVal) {
      const end = new Date(endDateVal);
      filteredData = filteredData.filter((d) => new Date(d.date) <= end);
    }

    if (filteredData.length === 1) {
      this.data1.labels = [
        formatDate(filteredData[0].date, 'dd-MM-yyyy', 'en-US'),
        formatDate(filteredData[0].date, 'dd-MM-yyyy', 'en-US'),
      ];
      this.data1.datasets[0].data = [
        Math.round(filteredData[0].quantity),
        Math.round(filteredData[0].quantity),
      ];
    } else {
      this.data1.labels = filteredData.map((element) => {
        return formatDate(element.date, 'dd-MM-yyyy', 'en-US');
      });
      this.data1.datasets[0].data = filteredData.map((element) => {
        return Math.round(element.quantity);
      });
    }

    this.renderLineChart();
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

  formatLongDate(date: any): string {
    const fecha = new Date(date);
    const options: Intl.DateTimeFormatOptions = {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    };
    return fecha.toLocaleDateString('es-ES', options);
  }
}
