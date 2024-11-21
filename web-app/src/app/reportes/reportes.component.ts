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
  dateForm: any;
  response: any;
  chartOptions: any;
  data: any;
  data1: any = { labels: [], datasets: [{ data: [] }] };
  options: any;

  data2: any;
  data3: any = { labels: [], datasets: [{ data: [] }] };
  options2: any;

  constructor(
    private formBuilder: FormBuilder,
    private reportesService: ReportesService
  ) {
    this.dateForm = this.formBuilder.group(
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
        validators: this.endDateGreaterThanStartDate(),
      }
    );
  }

  endDateGreaterThanStartDate(): ValidatorFn {
    return (control: AbstractControl) => {
      if (!this.dateForm) return null;
      const startDate = this.dateForm.get('startDate')?.value;
      const endDate = this.dateForm.get('endDate')?.value;
      if (!startDate || !endDate) {
        return { fechasIncompletas: true };
      }

      if (new Date(startDate) > new Date(endDate)) {
        return { rangoInvalido: true };
      }

      return null;
    };
  }

  ngOnInit(): void {
    this.options = {
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

    this.options2 = {
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

    this.onSubmit();
    this.fetchChartData();
    this.fetchLineChartData();
  }

  fetchChartData() {
    if (
      this.dateForm.get('startDate').value &&
      this.dateForm.get('endDate').value
    ) {
      this.reportesService
        .getTotalsByCategory(
          this.dateForm.get('startDate').value,
          this.dateForm.get('endDate').value
        )
        .subscribe({
          next: (data: any[]) => {
            this.data1.labels = data.map((element) => {
              return element[0].name;
            });
            this.data1.datasets[0].data = data.map((element) => {
              return element[1];
            });
            this.data1.datasets[0].label = '';
            this.data = { ...this.data1 };
            console.log(this.data1);
            console.log('Respuesta del servidorrr: ', data);
          },
          error: (error) => {
            console.error('Error al hacer la petición: ', error);
          },
          complete: () => {
            console.log('Petición completada');
          },
        });
    }
  }

  fetchLineChartData() {
    if (
      this.dateForm.get('startDate').value &&
      this.dateForm.get('endDate').value
    ) {
      const acc_total: any[] = [];
      this.reportesService
        .getPurchasesByRangeDate(
          this.dateForm.get('startDate').value,
          this.dateForm.get('endDate').value
        )
        .subscribe({
          next: (data: any[]) => {
            const groupedData: { [key: string]: number } = data.reduce(
              (acc, item) => {
                // Format the date as 'yyyy-MM-dd' for correct sorting
                const formattedDate = formatDate(item.date, 'yyyy-MM-dd', 'en-US');
                acc[formattedDate] = (acc[formattedDate] || 0) + item.total;
                return acc;
              },
              {}
            );
  
            const sortedData = Object.entries(groupedData)
              .map(([date, total]) => ({ date, total }))
              .sort((a, b) => a.date.localeCompare(b.date)); // Lexical sorting works with 'yyyy-MM-dd'
  
            // Format dates back to 'dd-MM-yyyy' for display purposes
            this.data3.labels = sortedData.map((element) =>
              formatDate(element.date, 'dd-MM-yyyy', 'en-US')
            );
  
            sortedData.reduce((acc, item) => {
              acc += item.total;
              acc_total.push(acc);
              return acc;
            }, 0);
  
            this.data3.datasets[0].data = acc_total;
            this.data3.datasets[0].label = 'Acumulativo';
            this.data2 = { ...this.data3 };
            console.log(this.data3);
          },
          error: (error) => {
            console.error('Error al hacer la petición: ', error);
          },
          complete: () => {
            console.log('Petición completada');
          },
        });
    }
  }
  

  onSubmit() {
    console.log(this.dateForm.get('startDate').value.toString());

    if (
      this.dateForm.get('startDate').value &&
      this.dateForm.get('endDate').value
    ) {
      const startDateDate = new Date(this.dateForm.get('startDate').value);
      const endDateDate = new Date(this.dateForm.get('endDate').value);
      const dateDiff = endDateDate.getTime() - startDateDate.getTime();
      this.response = this.reportesService
        .getPurchases(
          this.dateForm.get('startDate').value,
          this.dateForm.get('endDate').value
        )
        .subscribe({
          next: (data: any[]) => {
            const response = {
              total: 0,
              purchases: 0,
              averagePerMonth: 0,
              averagePerPurchase: 0,
            };

            response.total = data
              .reduce((acc, item) => acc + item.total, 0)
              .toFixed(2);
            response.purchases = data.length;
            response.averagePerMonth = +(response.total / 12).toFixed(2);
            response.averagePerPurchase = +(
              response.total / data.length
            ).toFixed(2);
            this.response = response;
          },
          error: (err) => {
            console.log('Error del servidor: ', err);
          },
          complete: () => {
            console.log('Peticion completada');
          },
        });
    }
  }
}
