import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Data Transformer", page_icon="📊", layout="wide")

st.title("📊 Data Transformer")
st.caption("Convert long-format to wide-format student course enrollment data")

uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx", "xls", "csv"])

if uploaded_file:
    # Read file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    st.success(f"Loaded {len(df)} records")

    # Group by student id + insignia
    grouped = df.groupby(["student id", "insignia", "insignianame"], sort=False)

    course_fields = ["registration_date", "coursename", "trainername", "coursecode", "startdate", "coursetype", "expiry_date"]
    
    rows = []
    max_courses = 0

    for (sid, ins, insname), group in grouped:
        row = {"student id": sid, "insignia": ins, "insignianame": insname}
        courses = group.reset_index(drop=True)
        max_courses = max(max_courses, len(courses))

        for i, (_, c) in enumerate(courses.iterrows()):
            if i > 0:
                try:
                    curr = pd.to_datetime(c["startdate"])
                    prev = pd.to_datetime(courses.iloc[i - 1]["startdate"])
                    gap = (curr - prev).days
                except:
                    gap = ""
                row[f"gap_days_{i}_to_{i+1}"] = gap

            for f in course_fields:
                row[f"{f}_{i+1}"] = c.get(f, "")

        rows.append(row)

    # Build output with correct column order
    headers = ["student id", "insignia", "insignianame"]
    for i in range(max_courses):
        if i > 0:
            headers.append(f"gap_days_{i}_to_{i+1}")
        for f in course_fields:
            headers.append(f"{f}_{i+1}")

    result_df = pd.DataFrame(rows, columns=headers)

    # Stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Students", len(result_df))
    col2.metric("Total Records", len(df))
    col3.metric("Max Courses", max_courses)
    col4.metric("Unique Insignias", df["insignia"].nunique())

    # Preview
    st.subheader("Transformed Data Preview")
    st.dataframe(result_df.head(10), use_container_width=True)

    if len(result_df) > 10:
        st.caption(f"Showing 10 of {len(result_df)} rows. Download to see all.")

    # Download
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        result_df.to_excel(writer, index=False, sheet_name="Transformed Data")
    
    original_name = uploaded_file.name.rsplit(".", 1)[0]
    st.download_button(
        "⬇️ Download Excel",
        data=output.getvalue(),
        file_name=f"{original_name}_transformed.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Upload an Excel file with columns: coursecode, startdate, registration_date, expiry_date, name, student id, coursename, coursetype, trainername, insignia, insignianame")
