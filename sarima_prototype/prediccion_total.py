import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
import pmdarima as pm
import argparse

def estimar(compras_route, ipc_route):
    compras_df = pd.read_excel(compras_route)
    ipc_df = pd.read_excel(ipc_route)

    compras_df['IPC'] = ipc_df['IPC']
    compras_df['Fecha'] = pd.to_datetime(compras_df['Fecha'])
    compras_df = compras_df.set_index('Fecha')
    compras_df = compras_df.asfreq('MS')

    train_size = len(compras_df) - 3
    train, test = compras_df[:train_size], compras_df[train_size:]

    auto_arima_model = pm.auto_arima(y=train['Total'],
                                x=train['IPC'],
                                seasonal=True,
                                m=12,
                                information_criterion="aic",
                                trace=True,
                                stepwise=True,
                                suppress_warnings=True)

    model = SARIMAX(endog=train['Total'],
                    exog=train['IPC'],
                    order=auto_arima_model.order,
                    seasonal_order=auto_arima_model.seasonal_order)
    model_fit = model.fit()

    forecast_steps = len(test)
    forecast = model_fit.forecast(steps = forecast_steps, exog=test['IPC'])

    forecast_index = test.index
    forecast_series = pd.Series(data=forecast, index=forecast_index)

    for fecha, forecast, actual, ipc in zip(test.index, forecast_series.round(2), test['Total'], test['IPC']):
        print(f"Fecha: {fecha.strftime('%m / %Y')}, Predicción: {forecast:.2f}, Original: {actual:.2f}, IPC: {ipc}")

    errors = forecast_series - test['Total']
    mae = np.mean(np.abs(errors))
    mse = np.mean(errors**2)
    rmse = np.sqrt(mse)
    mape = np.mean(np.abs(errors / test['Total'])) * 100

    print("Errores de Predicción:")
    print(f"MAE: {mae:.2f}")
    print(f"MSE: {mse:.2f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAPE: {mape:.2f}%")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Predicción de total de compra utilizando SARIMA")
    parser.add_argument('--compras', type=str, required=True, help="Ruta al archivo de compras")
    parser.add_argument('--ipc', type=str, required=True, help="Ruta al archivo de IPC")
    
    args = parser.parse_args()
    
    estimar(args.compras, args.ipc)