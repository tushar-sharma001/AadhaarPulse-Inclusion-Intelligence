import pandas as pd

# -------------------------------------------------
# Load raw CSVs
# -------------------------------------------------
enrol_paths = [
    "api_data_aadhar_enrolment_0_500000.csv",
    "api_data_aadhar_enrolment_500000_1000000.csv",
    "api_data_aadhar_enrolment_1000000_1006029.csv"
]

demo_paths = [
    "api_data_aadhar_demographic_0_500000.csv",
    "api_data_aadhar_demographic_500000_1000000.csv",
    "api_data_aadhar_demographic_1000000_1500000.csv",
    "api_data_aadhar_demographic_1500000_2000000.csv",
    "api_data_aadhar_demographic_2000000_2071700.csv"
]

enrol = pd.concat([pd.read_csv(p) for p in enrol_paths], ignore_index=True)
demo = pd.concat([pd.read_csv(p) for p in demo_paths], ignore_index=True)

# -------------------------------------------------
# Normalize column names
# -------------------------------------------------
enrol.columns = enrol.columns.str.strip().str.lower()
demo.columns = demo.columns.str.strip().str.lower()

# -------------------------------------------------
# Normalize state & district names
# -------------------------------------------------
for df in [enrol, demo]:
    df["state"] = df["state"].astype(str).str.strip().str.title()
    df["district"] = df["district"].astype(str).str.strip().str.title()

# -------------------------------------------------
# CREATE TOTAL ENROLMENT (FROM AGE COLUMNS)
# -------------------------------------------------
enrol_age_cols = ["age_0_5", "age_5_17", "age_18_greater"]

for col in enrol_age_cols:
    enrol[col] = pd.to_numeric(enrol[col], errors="coerce").fillna(0)

enrol["total_enrolment"] = enrol[enrol_age_cols].sum(axis=1)

# -------------------------------------------------
# AGGREGATE ENROLMENT AT DISTRICT LEVEL
# -------------------------------------------------
district_enrol = (
    enrol.groupby(["state", "district"])["total_enrolment"]
    .sum()
    .reset_index()
)

# -------------------------------------------------
# CREATE TOTAL POPULATION (FROM DEMO AGE COLUMNS)
# -------------------------------------------------
demo_age_cols = [c for c in demo.columns if c.startswith("demo_age")]

if not demo_age_cols:
    raise ValueError(
        f"No demographic age columns found. Columns: {list(demo.columns)}"
    )

for col in demo_age_cols:
    demo[col] = pd.to_numeric(demo[col], errors="coerce").fillna(0)

demo["population"] = demo[demo_age_cols].sum(axis=1)

# -------------------------------------------------
# AGGREGATE POPULATION AT DISTRICT LEVEL
# -------------------------------------------------
district_demo = (
    demo.groupby(["state", "district"])["population"]
    .sum()
    .reset_index()
)

# -------------------------------------------------
# MERGE ENROLMENT + POPULATION
# -------------------------------------------------
df = district_enrol.merge(
    district_demo,
    on=["state", "district"],
    how="left"
)

# -------------------------------------------------
# ADOPTION GAP SCORE (CORRECT LOGIC)
# -------------------------------------------------
df["adoption_gap_score"] = (
    1 - (df["total_enrolment"] / df["population"].replace(0, pd.NA))
)

df["adoption_gap_score"] = df["adoption_gap_score"].fillna(0).clip(0, 1)

# -------------------------------------------------
# RISK CLASSIFICATION
# -------------------------------------------------
df["risk_flag"] = pd.cut(
    df["adoption_gap_score"],
    bins=[-0.01, 0.3, 0.6, 1],
    labels=["Low Risk", "Medium Risk", "High Risk"]
)

# -------------------------------------------------
# SAVE DISTRICT INTELLIGENCE
# -------------------------------------------------
df.to_csv("district_intelligence.csv", index=False)

# -------------------------------------------------
# CREATE STATE-LEVEL INTELLIGENCE
# -------------------------------------------------
state_df = (
    df.groupby("state", as_index=False)
    .agg({
        "population": "sum",
        "total_enrolment": "sum"
    })
)

state_df["Adoption_Gap_Score"] = (
    1 - (state_df["total_enrolment"] / state_df["population"].replace(0, pd.NA))
)

state_df["Adoption_Gap_Score"] = state_df["Adoption_Gap_Score"].fillna(0).clip(0, 1)

state_df.rename(columns={"state": "State"}, inplace=True)

state_df.to_csv("state_intelligence.csv", index=False)

print("✅ district_intelligence.csv and state_intelligence.csv generated successfully")
