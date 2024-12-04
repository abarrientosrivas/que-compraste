import { Component } from '@angular/core';
import { NgxEchartsDirective } from 'ngx-echarts';
import { ReportesService } from './reportes.service';
import { formatDate } from '@angular/common';
import {
  FormBuilder,
  FormsModule,
  ValidatorFn,
  ReactiveFormsModule,
  Validators,
  AbstractControl,
} from '@angular/forms';
import { CommonModule } from '@angular/common';
import { ChartModule } from 'primeng/chart';
import { registerLocaleData } from '@angular/common';
import localeEs from '@angular/common/locales/es';

// Register the Spanish locale
registerLocaleData(localeEs, 'es-ES');

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    NgxEchartsDirective,
    FormsModule,
    ChartModule,
  ],
  templateUrl: './reportes.component.html',
  styleUrl: './reportes.component.css',
})
export class ReportesComponent {
  dateRangeForm: any;
  purchaseSummary: any;
  pieChartData: any;
  pieChartDataSource: any = { labels: [], datasets: [{ data: [] }] };
  pieChartConfig: any;

  lineChartData: any;
  lineChartDataSource: any = {
    labels: [],
    datasets: [{ data: [] }, { data: [] }],
  };
  lineChartConfig: any;

  constructor(
    private formBuilder: FormBuilder,
    private reportesService: ReportesService
  ) {
    this.dateRangeForm = this.formBuilder.group(
      {
        startDate: [
          formatDate(
            new Date(
              new Date().getTime() - 365 * 24 * 60 * 60 * 1000
            ).toString(),
            'YYYY-MM-dd',
            'en-US'
          ),
          Validators.required,
        ],
        endDate: [
          formatDate(new Date(), 'YYYY-MM-dd', 'en-US'),
          Validators.required,
        ],
      },
      {
        validators: this.validateEndDateAfterStartDate(),
      }
    );
  }

  validateEndDateAfterStartDate(): ValidatorFn {
    return (control: AbstractControl) => {
      if (!this.dateRangeForm) return null;
      const startDate = this.dateRangeForm.get('startDate')?.value;
      const endDate = this.dateRangeForm.get('endDate')?.value;
      if (!startDate || !endDate) {
        return { incompleteDates: true };
      }

      if (new Date(startDate) > new Date(endDate)) {
        return { invalidRange: true };
      }

      return null;
    };
  }

  ngOnInit(): void {
    this.pieChartConfig = {
      responsive: true,
      radius: '75%',
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            usePointStyle: true,
            color: '#000000',
          },
        },
      },
    };

    this.lineChartConfig = {
      maintainAspectRatio: false,
      aspectRatio: 0.6,
      plugins: {
        legend: {
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
            drawBorder: false,
          },
        },
        y: {
          ticks: {
            color: 'black',
          },
          grid: {
            color: '#DAD8C9',
            drawBorder: false,
          },
        },
      },
    };

    this.submitForm();
    this.loadLineChartData();
  }

  loadPieChartData() {
    if (
      this.dateRangeForm.get('startDate').value &&
      this.dateRangeForm.get('endDate').value
    ) {
      const endDate = new Date(this.dateRangeForm.get('endDate').value);
      endDate.setDate(endDate.getDate() + 1);

      this.reportesService
        .getTotalsByCategory(
          this.dateRangeForm.get('startDate').value,
          endDate.toISOString().split('T')[0]
        )
        .subscribe({
          next: (categories: any[]) => {
            if (categories.length === 0) {
              this.pieChartData = { labels: [], datasets: [{ data: [] }] };
              return;
            }

            this.pieChartDataSource.labels = categories.map((category) => {
              return category[0].name_es_es;
            });
            this.pieChartDataSource.datasets[0].data = categories.map(
              (category) => {
                return category[1];
              }
            );
            this.pieChartDataSource.datasets[0].label = '';
            this.pieChartData = { ...this.pieChartDataSource };
            console.log('Server response: ', categories);
          },
          error: (error) => {
            console.error('Request error: ', error);
          },
          complete: () => {
            console.log('Request completed');
          },
        });
    }
  }

  loadLineChartData() {
    if (
      this.dateRangeForm.get('startDate').value &&
      this.dateRangeForm.get('endDate').value
    ) {
      const accumulatedTotals: any[] = [];
      this.reportesService
        .getPurchasesByRangeDate(
          this.dateRangeForm.get('startDate').value,
          this.dateRangeForm.get('endDate').value
        )
        .subscribe({
          next: (purchases: any[]) => {
            const groupedPurchases: { [key: string]: number } =
              purchases.reduce((acc, purchase) => {
                const formattedDate = formatDate(
                  purchase.date,
                  'yyyy-MM',
                  'en-US'
                );
                acc[formattedDate] = (acc[formattedDate] || 0) + purchase.total;
                return acc;
              }, {});

            const monthlyTotals = purchases.reduce((acc, purchase) => {
              const month = formatDate(purchase.date, 'yyyy-MM', 'en-US');
              acc[month] = (acc[month] || 0) + purchase.total;
              return acc;
            }, {});

            const sortedMonthlyTotals = Object.entries(monthlyTotals)
              .map(([date, total]) => ({ date, total }))
              .sort((a, b) => a.date.localeCompare(b.date));
            this.lineChartDataSource.datasets[1].data = sortedMonthlyTotals.map(
              (entry) => entry.total
            );

            this.lineChartDataSource.datasets[1].label = 'Mensual';

            const sortedPurchases = Object.entries(groupedPurchases)
              .map(([date, total]) => ({ date, total }))
              .sort((a, b) => a.date.localeCompare(b.date));

            this.lineChartDataSource.labels = sortedPurchases.map((entry) =>
              formatDate(entry.date, 'MM-yyyy', 'en-US')
            );

            sortedPurchases.reduce((acc, entry) => {
              acc += entry.total;
              accumulatedTotals.push(acc);
              return acc;
            }, 0);

            this.lineChartDataSource.datasets[0].data = accumulatedTotals;
            this.lineChartDataSource.datasets[0].label = 'Acumulado';
            this.lineChartData = { ...this.lineChartDataSource };
          },
          error: (error) => {
            console.error('Request error: ', error);
          },
          complete: () => {
            console.log('Request completed');
          },
        });
    }
  }

  submitForm() {
    if (
      this.dateRangeForm.get('startDate').value &&
      this.dateRangeForm.get('endDate').value
    ) {
      const startDate = new Date(this.dateRangeForm.get('startDate').value);
      const endDate = new Date(this.dateRangeForm.get('endDate').value);
      endDate.setDate(endDate.getDate() + 1);
      this.purchaseSummary = null;
      this.purchaseSummary = this.reportesService
        .getPurchasesByRangeDate(
          this.dateRangeForm.get('startDate').value,
          endDate.toISOString().split('T')[0]
        )
        .subscribe({
          next: (purchases: any[]) => {
            this.loadPieChartData();
            if (purchases.length === 0) {
              this.purchaseSummary = null;
              return;
            }

            const summary = {
              totalSpent: 0,
              totalPurchases: 0,
              averageMonthlySpending: 0,
              averageSpendingPerPurchase: 0,
              totalProducts: 0,
              averageTotalProductsPerPurchase: 0,
              averageDaysBetweenPurchases: 0,
            };

            summary.totalSpent = purchases
              .reduce((acc, purchase) => acc + purchase.total, 0)
              .toFixed(2);

            summary.totalPurchases = purchases.length;

            summary.averageMonthlySpending = +(summary.totalSpent / 12).toFixed(
              2
            );

            summary.averageSpendingPerPurchase = +(
              summary.totalSpent / purchases.length
            ).toFixed(2);

            summary.totalProducts = purchases
              .reduce((acc, purchase) => {
                const quantity = purchase.items.reduce(
                  (acc_quantity: any, item: any) => {
                    acc_quantity += item.quantity;
                    return acc_quantity;
                  },
                  0
                );
                return (acc += quantity);
              }, 0)
              .toFixed(2);

            summary.averageTotalProductsPerPurchase = +(
              summary.totalProducts / purchases.length
            ).toFixed(2);

            purchases.sort(
              (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
            );

            const timeDifferences = purchases
              .map((_, i) =>
                i > 0
                  ? new Date(purchases[i].date).getTime() -
                    new Date(purchases[i - 1].date).getTime()
                  : 0
              )
              .slice(1);

            const averageTimeBetweenPurchases =
              timeDifferences.reduce((acc, time) => acc + time, 0) /
              timeDifferences.length;

            summary.averageDaysBetweenPurchases = +(
              averageTimeBetweenPurchases /
              (1000 * 60 * 60 * 24)
            ).toFixed(2);

            const topProducts = purchases.reduce((acc, purchase) => {
              purchase.items.forEach((item: any) => {
                if (!acc[item.read_product_text]) {
                  acc[item.read_product_text] = 0;
                }
                acc[item.read_product_text] += item.quantity;
              });
              return acc;
            }, {} as Record<string, number>);

            const sortedTopProducts = Object.entries(topProducts)
              .map(([name, quantity]) => ({
                name,
                quantity: quantity as number,
              }))
              .sort((a, b) => b.quantity - a.quantity)
              .slice(0, 10);

            console.log(sortedTopProducts);

            this.purchaseSummary = summary;
          },
          error: (err) => {
            console.log('Server error: ', err);
          },
          complete: () => {
            console.log('Request completed');
          },
        });
    }
  }
}
