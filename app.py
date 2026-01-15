import streamlit as st
import pandas as pd
import plotly.express as px
import json

st.set_page_config(
    page_title="AadhaarPulse",
    layout="wide",
    initial_sidebar_state="collapsed"
)


st.markdown("""
<style>
body { background-color: #0e1117; }
.big-title { font-size: 44px; font-weight: 800; margin-bottom: 5px; }
.sub-title { font-size: 18px; color: #9ca3af; margin-bottom: 35px; }
.kpi-card {
    background: linear-gradient(135deg, #1f2937, #111827);
    padding: 22px;
    border-radius: 18px;
    text-align: center;
    box-shadow: 0 10px 25px rgba(0,0,0,0.35);
}
.kpi-title { font-size: 14px; color: #9ca3af; }
.kpi-value { font-size: 36px; font-weight: 700; }
.section-divider { border: 1px solid #1f2937; margin: 45px 0; }
</style>
""", unsafe_allow_html=True)

# HEADER
st.markdown("""
<div class="big-title">AadhaarPulse</div>
<div class="sub-title">
Tracking Aadhaar Adoption, Inclusion Risk & Future Enrolment Demand Across India
</div>
""", unsafe_allow_html=True)

# LOAD DATA
district = pd.read_csv("district_intelligence.csv")
state_df = pd.read_csv("state_intelligence.csv")
forecast_df = pd.read_csv("state_forecast_12_months.csv")

state_name_fix = {
    "Jammu & Kashmir": "Jammu and Kashmir",
    "Andaman & Nicobar Islands": "Andaman and Nicobar",
    "Dadra & Nagar Haveli And Daman & Diu": "Dadra and Nagar Haveli"
}

state_df["State"] = state_df["State"].replace(state_name_fix)


district["district"] = district["district"].astype(str)
district = district[~district["district"].str.isnumeric()]
district = district[district["district"] != "100000"]

district["bubble_size"] = (
    district["population"]
    .fillna(district["population"].median())
    .clip(lower=1)
)

c1, c2, c3, c4 = st.columns(4)

c1.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total Districts</div><div class='kpi-value'>{len(district)}</div></div>", unsafe_allow_html=True)
c2.markdown(f"<div class='kpi-card'><div class='kpi-title'>High Risk Districts</div><div class='kpi-value'>{(district['risk_flag']=='High Risk').sum()}</div></div>", unsafe_allow_html=True)
c3.markdown(f"<div class='kpi-card'><div class='kpi-title'>Medium Risk Districts</div><div class='kpi-value'>{(district['risk_flag']=='Medium Risk').sum()}</div></div>", unsafe_allow_html=True)
c4.markdown(f"<div class='kpi-card'><div class='kpi-title'>Avg Adoption Gap</div><div class='kpi-value'>{state_df['Adoption_Gap_Score'].mean():.2f}</div></div>", unsafe_allow_html=True)

# TOP 10 HIGH-RISK DISTRICTS
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.subheader("🚨 Top-10 Highest Aadhaar Adoption Risk Districts")

top10 = district.sort_values("adoption_gap_score", ascending=False).head(10)
top10["Rank"] = range(1, len(top10) + 1)

st.dataframe(
    top10[["Rank","state","district","adoption_gap_score","risk_flag"]]
    .rename(columns={
        "state":"State",
        "district":"District",
        "adoption_gap_score":"Adoption Gap",
        "risk_flag":"Risk Level"
    }),
    use_container_width=True,
    height=360
)

# INDIA MAP
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.subheader("State-wise Aadhaar Adoption Gap")

with open("india_states.geojson", "r", encoding="utf-8") as f:
    india_geojson = json.load(f)

fig_map = px.choropleth(
    state_df,
    geojson=india_geojson,
    locations="State",
    featureidkey="properties.NAME_1",
    color="Adoption_Gap_Score",
    color_continuous_scale="RdYlGn_r",
    range_color=(0, 1)
)

fig_map.update_geos(fitbounds="locations", visible=False)
fig_map.update_layout(paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", font_color="white")
st.plotly_chart(fig_map, use_container_width=True)

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.subheader("🗺️ Quick District Comparison (From Map View)")

map_state = st.selectbox("Select State", sorted(district["state"].unique()), key="map_state")
map_df = district[district["state"] == map_state]

district_opts = sorted(map_df["district"].unique())

if len(district_opts) >= 2:
    col1, col2 = st.columns(2)
    with col1:
        d1m = st.selectbox("District A", district_opts, key="map_d1")
    with col2:
        d2m = st.selectbox("District B", district_opts, index=1, key="map_d2")

    if d1m != d2m:
        a = map_df[map_df["district"] == d1m].iloc[0]
        b = map_df[map_df["district"] == d2m].iloc[0]

        st.dataframe(pd.DataFrame({
            "Metric":["Population","Enrolments","Adoption Gap","Risk"],
            d1m:[a["population"],a["total_enrolment"],round(a["adoption_gap_score"],2),a["risk_flag"]],
            d2m:[b["population"],b["total_enrolment"],round(b["adoption_gap_score"],2),b["risk_flag"]]
        }), use_container_width=True)
else:
    st.info("Not enough districts in this state for comparison.")

# RISK HEATMAP
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.subheader("🔥 Risk Distribution Heatmap")

risk_heatmap = (
    district.groupby(["state","risk_flag"])
    .size()
    .reset_index(name="district_count")
)

fig_heat = px.density_heatmap(
    risk_heatmap,
    x="risk_flag",
    y="state",
    z="district_count",
    color_continuous_scale="Reds"
)

fig_heat.update_layout(paper_bgcolor="#0e1117", plot_bgcolor="#0e1117", font_color="white")
st.plotly_chart(fig_heat, use_container_width=True)

# DISTRICT DRILL-DOWN
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.subheader("🧭 District Drill-Down Analysis")

state_sel = st.selectbox(
    "Select State",
    sorted(district["state"].unique()),
    key="dd_state"
)

state_df_dd = district[district["state"] == state_sel]

district_sel = st.selectbox(
    "Select District",
    sorted(state_df_dd["district"].unique()),
    key="dd_district"
)

district_row = state_df_dd[state_df_dd["district"] == district_sel].iloc[0]

bar_df = pd.DataFrame({
    "Metric": ["Population", "Total Enrolments"],
    "Value": [
        district_row["population"],
        district_row["total_enrolment"]
    ]
})

fig_bar = px.bar(
    bar_df,
    x="Metric",
    y="Value",
    text="Value",
    title=f"Aadhaar Coverage Overview — {district_sel}"
)

fig_bar.update_layout(
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font_color="white"
)

st.plotly_chart(fig_bar, use_container_width=True)

fig_scatter = px.scatter(
    state_df_dd,
    x="total_enrolment",
    y="adoption_gap_score",
    color="risk_flag",
    size="bubble_size",
    hover_name="district",
    title=f"District Risk Positioning — {state_sel}"
)

fig_scatter.update_layout(
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font_color="white",
    xaxis_title="Total Enrolments",
    yaxis_title="Adoption Gap Score"
)

st.plotly_chart(fig_scatter, use_container_width=True)

# DISTRICT COMPARISON
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.subheader("⚖️ District Comparison")

district_options = sorted(state_df_dd["district"].unique())

if len(district_options) < 2:
    st.warning("Not enough districts in this state for comparison.")
else:
    col1, col2 = st.columns(2)
    with col1:
        d1 = st.selectbox("District A", district_options, index=0, key="cmp_d1")
    with col2:
        d2 = st.selectbox("District B", district_options, index=1, key="cmp_d2")

    if d1 != d2:
        a = state_df_dd[state_df_dd["district"] == d1].iloc[0]
        b = state_df_dd[state_df_dd["district"] == d2].iloc[0]

        st.dataframe(pd.DataFrame({
            "Metric":["Population","Enrolments","Adoption Gap","Risk"],
            d1:[a["population"],a["total_enrolment"],round(a["adoption_gap_score"],2),a["risk_flag"]],
            d2:[b["population"],b["total_enrolment"],round(b["adoption_gap_score"],2),b["risk_flag"]]
        }), use_container_width=True)


# FORECAST
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.subheader("📈 Aadhaar Enrolment Forecast")

fs = st.selectbox("Select State for Forecast", sorted(forecast_df["state"].unique()), key="fc_state")
fs_df = forecast_df[forecast_df["state"] == fs]

fig_forecast = px.line(
    fs_df,
    x="ds",
    y="yhat",
    labels={
        "ds": "Month",
        "yhat": "Predicted Aadhaar Enrolments"
    },
    title=f"12-Month Aadhaar Enrolment Forecast — {fs}"
)

fig_forecast.update_layout(
    paper_bgcolor="#0e1117",
    plot_bgcolor="#0e1117",
    font_color="white",
    xaxis_title="Forecast Period",
    yaxis_title="Expected Aadhaar Enrolments"
)

fig_forecast.update_yaxes(
    zeroline=True,
    zerolinecolor="gray"
)

st.plotly_chart(fig_forecast, use_container_width=True)


# FOOTER
st.markdown("""
<hr style="border:1px solid #1f2937;">
<div style="text-align:center;color:#9ca3af;font-size:14px;">
AadhaarPulse • UIDAI Data Hackathon 2026
</div>
""", unsafe_allow_html=True)
