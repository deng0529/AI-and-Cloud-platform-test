import streamlit as st
from google.cloud import bigquery
import pandas as pd
# import altair as alt
from google.oauth2 import service_account

# for cloud run
credentials = service_account.Credentials.from_service_account_info(
    st.secrets["gcp_service_account"]
)

client = bigquery.Client(
    credentials=credentials,
    project=credentials.project_id,
)

# -----------------------------
# BigQuery client
# -----------------------------
# for locally run
# client = bigquery.Client()
# query = """
#            SELECT *
#            FROM `building-heating-system.bhs.buildingB`
#            LIMIT 100
# """
#
# df = client.query(query).to_dataframe()
# print(df)
#
# st.dataframe(df)
st.title("Building Temperature Dashboard based on Bigquery + Google Cloud")

# Building list for selector
buildings = ["buildingA", "buildingB"]

# Streamlit selector
selected_building = st.selectbox(
    "Select a building",
    buildings
)

# Build table name dynamically
PROJECT_ID = "building-heating-system"
DATASET_ID = "bhs"

table_id = f"{PROJECT_ID}.{DATASET_ID}.{selected_building}"

query = f"""
SELECT
  ext AS ext_temp,
  `temp_0` AS indoor_temp,
  target_temp,
  sample_time,
  zoneid,
FROM `{table_id}`
"""

df = client.query(query).to_dataframe()

# Show table
st.dataframe(df)

# -----------------------------
# Step 3: Select zone
# -----------------------------
zones = sorted(df["zoneid"].unique())
zone = st.selectbox("Select Zone", zones)

zone_df = df[df["zoneid"] == zone]
# ext, temp.0, target_temp, sample_time

def remove_outliers_iqr(df, columns):
    clean_df = df.copy()
    for col in columns:
        q1 = clean_df[col].quantile(0.25)
        q3 = clean_df[col].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        clean_df = clean_df[(clean_df[col] >= lower) & (clean_df[col] <= upper)]
    return clean_df

remove_outliers = st.checkbox("Remove outliers", value=True)

if remove_outliers:
    df = remove_outliers_iqr(
        df,
        columns=["ext_temp", "indoor_temp"]
    )


# df already contains:
# columns: sample_time, ext_temp, indoor_temp, target_temp

# Ensure datetime
df["sample_time"] = pd.to_datetime(df["sample_time"])
df = df.sort_values("sample_time")
 # add time range slider
start_time, end_time = st.slider(
    "Select time range",
    min_value=df["sample_time"].min().to_pydatetime(),
    max_value=df["sample_time"].max().to_pydatetime(),
    value=(
        df["sample_time"].min().to_pydatetime(),
        df["sample_time"].max().to_pydatetime(),
    ),
    format="YYYY-MM-DD HH:mm"
)

filtered_df = df[
    (df["sample_time"] >= start_time) &
    (df["sample_time"] <= end_time)
]

# Line chart
# ---------------------------
plot_cols = ["ext_temp", "indoor_temp", 'target_temp']
available_cols = [c for c in plot_cols if c in filtered_df.columns]
timestamp_col = 'sample_time'
if len(available_cols) > 0:
    st.subheader("Temperature Over Time")
    st.line_chart(filtered_df.set_index(timestamp_col)[available_cols])
else:
    st.warning("No temperature columns available to plot.")

# Transform to long format for Altair
# df_long = df.melt(
#     id_vars=["sample_time"],
#     value_vars=["ext_temp", "indoor_temp", "target_temp"],
#     var_name="temperature_type",
#     value_name="temperature"
# )

# Altair line chart
# chart = (
#     alt.Chart(df_long)
#     .mark_line()
#     .encode(
#         x=alt.X("sample_time:T", title="Date"),
#         y=alt.Y("temperature:Q", title="Temperature"),
#         color=alt.Color("temperature_type:N", title="Type"),
#         tooltip=["sample_time:T", "temperature_type:N", "temperature:Q"]
#     )
#     .properties(
#         width=900,
#         height=400
#     )
#     .interactive()
# )
#
# st.altair_chart(chart, use_container_width=True)