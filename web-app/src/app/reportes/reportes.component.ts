import { Component } from '@angular/core';
import { NgxEchartsDirective, provideEcharts } from 'ngx-echarts';
import { EChartsOption } from 'echarts';
import { ReportesService } from '../reportes.service';

@Component({
  selector: 'app-reportes',
  standalone: true,
  imports: [NgxEchartsDirective],
  templateUrl: './reportes.component.html',
  styleUrl: './reportes.component.css',
  providers: [provideEcharts()],
})
export class ReportesComponent {
  constructor(private reportesService: ReportesService) {}

  chartOptions: any;

  ngOnInit(): void {
    this.fetchChartData();
  }

  fetchChartData() {
    this.reportesService.getTotalsByCategory('', '').subscribe({
      next: (data) => {
        console.log('Respuesta del servidor:', data);
        this.setChartOptions(data);
      },
      error: (error) => {
        console.error('Error al hacer la petición:', error);
      },
      complete: () => {
        console.log('Petición completada');
      },
    });
  }

  setChartOptions(data: any[]) {
    this.chartOptions = {
      title: {
        text: 'Total por Categoria',
        left: 'center',
      },
      legend: {
        data: data.map((value) => value.name),
        show: true,
        type: 'scroll',
      },
      tooltip: {},
      series: [
        {
          name: 'Total',
          type: 'pie',
          data: data,
          emphasis: {
            itemStyle: {
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowColor: 'rgba(0, 0, 0, 0.5)',
            },
          },
        },
      ],
      media: [
        {
          query: {
            maxWidth: 935,
          },
          option: {
            legend: {
              orient: 'horizontal',
              bottom: 50,
              right: 10,
            },
            series: [
              {
                radius: '30%',
                center: ['50%', '20%'],
              },
            ],
          },
        },
        {
          query: {
            minWidth: 936,
            maxWidth: 1115,
          },
          option: {
            legend: {
              orient: 'horizontal',
              bottom: 30,
              right: 10,
            },
            series: [
              {
                radius: '40%',
                center: ['50%', '30%'],
              },
            ],
          },
        },
        {
          option: {
            legend: {
              orient: 'vertical',
              align: 'left',
              left: 'left',
              top: 60,
            },
            series: [
              {
                center: ['50%', '50%'],
                radius: '55%',
                top: 40,
              },
            ],
          },
        },
      ],
    };
  }
}
