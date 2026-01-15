import pandas as pd
from prophet import Prophet
from data_loader import load_enrolment

paths = [
    "api_data_aadhar_enrolment_0_500000.csv",
    "api_data_aadhar_enrolment_500000_1000000.csv",
    "api_data_aadhar_enrolment_1000000_1006029.csv"
]

df = load_enrolment(paths)

state_ts = (
    df.dropna(subset=["date"])
    .groupby(["state","date"])["total_enrolment"]
    .sum()
    .reset_index()
)

forecasts = []
for state in state_ts["state"].unique():
    ts = state_ts[state_ts["state"]==state][["date","total_enrolment"]]
    ts = ts.rename(columns={"date":"ds","total_enrolment":"y"})
    if len(ts)<8 or ts["y"].sum()<=0:
        continue
    model = Prophet(yearly_seasonality=True)
    model.fit(ts)
    future = model.make_future_dataframe(periods=12, freq="M")
    fc = model.predict(future)[["ds","yhat"]]
    fc["state"] = state
    forecasts.append(fc)

if forecasts:
    pd.concat(forecasts).to_csv("state_forecast_12_months.csv", index=False)
