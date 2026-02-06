import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Student Course Transformer", layout="wide")
st.title("📊 Student Course Data Transformer")
st.markdown("Upload your Excel file to transform student enrollment data from long to wide format.")

uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("Raw Data Preview")
    st.dataframe(df.head(10), use_container_width=True)

    date_cols = ["startdate", "registration_date", "expiry_date"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")

    grouped = df.groupby(["student id", "insignia", "insignianame"])
    max_courses = grouped.size().max()

    st.info(f"Found **{grouped.ngroups}** students with up to **{max_courses}** courses each.")

    course_fields = ["registration_date", "coursename", "trainername", "coursecode", "startdate", "coursetype", "expiry_date"]

    headers = ["student id", "insignia", "insignianame"]
    for i in range(max_courses):
        if i > 0:
            headers.append(f"gap_days_{i}_to_{i+1}")
        for field in course_fields:
            headers.append(field)

    rows = []
    for (sid, insignia, insignianame), group in grouped:
        row = [sid, insignia, insignianame]
        courses = group.sort_values("startdate").reset_index(drop=True)
        for i in range(max_courses):
            if i > 0:
                if i < len(courses) and i - 1 < len(courses):
                    try:
                        curr = pd.to_datetime(courses.loc[i, "startdate"])
                        prev = pd.to_datetime(courses.loc[i - 1, "startdate"])
                        gap = (curr - prev).days
                        row.append(gap)
                    except:
                        row.append("")
                else:
                    row.append("")
            if i < len(courses):
                for field in course_fields:
                    row.append(courses.loc[i, field] if field in courses.columns else "")
            else:
                row.extend([""] * len(course_fields))
        rows.append(row)

    result_df = pd.DataFrame(rows, columns=headers)

    st.subheader("Transformed Data Preview")
    st.dataframe(result_df.head(10), use_container_width=True)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        result_df.to_excel(writer, index=False, sheet_name="Transformed")
    output.seek(0)

    st.download_button(
        label="📥 Download Transformed Excel",
        data=output,
        file_name="transformed_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
