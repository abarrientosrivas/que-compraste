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
    this.loadPieChartData();
    this.loadLineChartData();
  }

  loadPieChartData() {
    if (
      this.dateRangeForm.get('startDate').value &&
      this.dateRangeForm.get('endDate').value
    ) {
      this.reportesService
        .getTotalsByCategory(
          this.dateRangeForm.get('startDate').value,
          this.dateRangeForm.get('endDate').value
        )
        .subscribe({
          next: (categories: any[]) => {
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
    console.log(this.dateRangeForm.get('startDate').value.toString());

    if (
      this.dateRangeForm.get('startDate').value &&
      this.dateRangeForm.get('endDate').value
    ) {
      const start = new Date(this.dateRangeForm.get('startDate').value);
      const end = new Date(this.dateRangeForm.get('endDate').value);
      const dateDifference = end.getTime() - start.getTime();
      this.purchaseSummary = this.reportesService
        .getPurchases(
          this.dateRangeForm.get('startDate').value,
          this.dateRangeForm.get('endDate').value
        )
        .subscribe({
          next: (purchases: any[]) => {
            const summary = {
              totalSpent: 0,
              totalPurchases: 0,
              averageMonthlySpending: 0,
              averageSpendingPerPurchase: 0,
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
