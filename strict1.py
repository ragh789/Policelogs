import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from streamlit_option_menu import option_menu

# ----------------- Page Configuration ----------------- #
st.set_page_config(page_title="Traffic Stop Dashboard", layout="wide")

# ----------------- Initialize DB Connection ----------------- #
@st.cache_resource
def get_connection():
    return sqlite3.connect("traffic_stops.db", check_same_thread=False)

conn = get_connection()

# ----------------- Fetch Data ----------------- #
@st.cache_data
def fetch_data():
    return pd.read_sql("SELECT * FROM police", conn, parse_dates=['timestamp'])

data = fetch_data()

# ----------------- Sidebar Navigation ----------------- #
with st.sidebar:
    selected = option_menu("Main Menu", ["Home", "Generate Summary", "SQL Queries"],
                           icons=["house", "chat-left-dots", "database"], default_index=0)

# ----------------- Home ----------------- #
if selected == "Home":
    st.title("🚓 Digital Ledger for Police Post Logs")
    st.markdown("""
    ## 📜 About This Dashboard
    Welcome to the Digital Ledger for Police Post Logs.

    ### 📌 Features:
    - View and filter traffic stop records
    - Analyze violations by type and frequency
    - Monitor trends by driver demographics
    - Search data by timestamp, gender, or outcome

    ### 🔐 Data Source:
    Local SQLite database (traffic_stops.db)
    """)

    if not data.empty:
        total_stops = len(data)
        total_arrests = data[data['stop_outcome'].str.contains('arrest', case=False, na=False)].shape[0]
        total_warnings = data[data['stop_outcome'].str.contains('warning', case=False, na=False)].shape[0]

        st.markdown("## 📊 Key Metrics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Police Stops", total_stops)
        col2.metric("Total Arrests", total_arrests)
        col3.metric("Total Warnings", total_warnings)

# ----------------- Generate Summary ----------------- #
elif selected == "Generate Summary":
    st.header("🦳 Generate Summary from Stop Details")

    with st.form("summary_form"):
        col1, col2 = st.columns(2)
        with col1:
            input_country = st.selectbox("Country Name", [""] + sorted(data['country_name'].dropna().unique().tolist()))
            input_gender = st.selectbox("Driver Gender", ["", "M", "F"])
            input_age = st.text_input("Driver Age")
        with col2:
            input_date = st.date_input("Stop Date (YYYY-MM-DD)")
            input_time_str = st.text_input("Stop Time (hh:mm:ss)", placeholder="e.g. 00:01:00")

        submit = st.form_submit_button("Generate Stop Summary")

    if submit:
        if all([input_country, input_gender, input_age, input_date, input_time_str]):
            try:
                age = int(input_age)
                timestamp_str = f"{input_date} {input_time_str}"
                stop_dt = pd.to_datetime(timestamp_str, errors='raise')
                filtered = data[
                    (data['country_name'] == input_country) &
                    (data['driver_gender'].str.lower() == input_gender.lower()) &
                    (data['driver_age'] == age) &
                    (data['timestamp'] == stop_dt)
                ]

                if filtered.empty:
                    st.info("No matching record found for the given details.")
                else:
                    row = filtered.iloc[0]
                    time_fmt = row['timestamp'].strftime('%I:%M %p')
                    gender_text = "male" if row['driver_gender'].upper() == 'M' else "female"
                    search_text = "A search was conducted" if row['search_conducted'] else "No search was conducted"
                    drug_text = "was drug-related" if row['drugs_related_stop'] else "was not drug-related"
                    st.success(
                        f"A {row['driver_age']}-year-old {gender_text} driver was stopped "
                        f"for {row['violation_raw']} at {time_fmt}. {search_text}, "
                        f"and they received a {row['stop_outcome'].lower()}. The stop lasted {row['stop_duration']} "
                        f"and {drug_text}."
                    )
            except Exception as e:
                st.error(f"❌ Invalid input format: {e}")
        else:
            st.warning("⚠ Please fill in all fields before submitting.")

# ----------------- SQL Queries Section ----------------- #
elif selected == "SQL Queries":
    st.header("🧠 SQL Query Explorer")

    sql_questions = [
        "What are the top 10 vehicle_Number involved in drug-related stops?",
        "Which vehicles were most frequently searched?",
        "Which driver age group had the highest arrest rate?",
        "What is the gender distribution of drivers stopped in each country?",
        "Which race and gender combination has the highest search rate?",
        "What time of day sees the most traffic stops?",
        "What is the average stop duration for different violations?",
        "Are stops during the night more likely to lead to arrests?",
        "Which violations are most associated with searches or arrests?",
        "Which violations are most common among younger drivers (<25)?",
        "Is there a violation that rarely results in search or arrest?",
        "Which countries report the highest rate of drug-related stops?",
        "What is the arrest rate by country and violation?",
        "Which country has the most stops with search conducted?",
        "Yearly Breakdown of Stops and Arrests by Country?",
        "Driver Violation Trends Based on Age and Race?",
        "Time Period Analysis of Stops?",
        "Violations with High Search and Arrest Rates?",
        "Driver Demographics by Country?",
        "Top 5 Violations with Highest Arrest Rates?"
    ]

    sql_queries = {
        sql_questions[0]: """
            SELECT vehicle_number, COUNT(*) AS stop_count
            FROM police
            WHERE drugs_related_stop = 1 AND vehicle_number IS NOT NULL
            GROUP BY vehicle_number
            ORDER BY stop_count DESC,vehicle_number ASC
            LIMIT 10;
        """,
        sql_questions[1]: """
            SELECT vehicle_number, COUNT(*) AS search_count
            FROM police
            WHERE search_conducted = 1 AND vehicle_number IS NOT NULL
            GROUP BY vehicle_number
            ORDER BY search_count DESC, vehicle_number ASC
            LIMIT 10;
        """,
        sql_questions[2]: """
            SELECT driver_age,
            ROUND((SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT()) * 100, 2) AS arrest_rate
            FROM police
            GROUP BY driver_age
            ORDER BY arrest_rate DESC
            LIMIT 1;
        """,
        sql_questions[3]: """
            SELECT country_name, driver_gender, COUNT(*) AS total_stops
            FROM police
            GROUP BY country_name, driver_gender
            ORDER BY country_name;
        """,
        sql_questions[4]: """
           SELECT driver_race, driver_gender,
           ROUND((SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) * 100, 2) AS search_rate
           FROM police
           GROUP BY driver_race, driver_gender
           ORDER BY search_rate DESC
           LIMIT 1;
        """,
        sql_questions[5]: """
            SELECT strftime('%H', timestamp) AS hour,
            COUNT(*) AS stop_count
            FROM police
            GROUP BY hour
            ORDER BY stop_count DESC
            LIMIT 1;
        """,
        sql_questions[6]: """
            SELECT violation, 
                   ROUND(AVG(CASE 
                               WHEN stop_duration = '0-15 Min' THEN 7.5
                               WHEN stop_duration = '16-30 Min' THEN 23
                               WHEN stop_duration = '30+ Min' THEN 35
                               ELSE NULL
                             END), 2) AS avg_duration
            FROM police
            GROUP BY violation
            ORDER BY avg_duration DESC;
        """,
        sql_questions[7]: """
            SELECT
            CASE
            WHEN CAST(strftime('%H', timestamp) AS INTEGER) BETWEEN 0 AND 5 THEN 'Night'
            ELSE 'Day'
            END AS period,
            ROUND(
            (SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT()) * 100,
            2
            ) AS arrest_rate
            FROM police
            GROUP BY period;
        """,
        sql_questions[8]: """
            SELECT violation,
                   SUM(CASE WHEN search_conducted THEN 1 ELSE 0 END) AS search_count,
                   SUM(CASE WHEN is_arrested THEN 1 ELSE 0 END) AS arrest_count
            FROM police
            GROUP BY violation
            ORDER BY arrest_count DESC;
        """,
        sql_questions[9]: """
            SELECT violation, COUNT(*) AS total
            FROM police
            WHERE driver_age < 25
            GROUP BY violation
            ORDER BY total DESC
            LIMIT 1;
        """,
        sql_questions[10]: """
            SELECT violation,
            COUNT(*) AS total_stops,
            ROUND(
            (SUM(CASE WHEN search_conducted = 1 OR is_arrested = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) * 100, 
            2
            ) AS action_rate
            FROM police
            GROUP BY violation
            HAVING action_rate < 20
            ORDER BY action_rate ASC;
        """,
        sql_questions[11]: """
            SELECT country_name,
            ROUND((SUM(CASE WHEN drugs_related_stop = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT()) * 100, 2) AS drug_rate
            FROM police
            GROUP BY country_name
            ORDER BY drug_rate DESC
            LIMIT 1;
        """,
        sql_questions[12]: """
            SELECT country_name,
            violation,
            ROUND((SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT()) * 100, 2) AS arrest_rate
            FROM police
            GROUP BY country_name, violation
            ORDER BY arrest_rate DESC;
        """,
        sql_questions[13]: """
            SELECT country_name, COUNT(*) AS total, SUM(CASE WHEN search_conducted THEN 1 ELSE 0 END) AS searches
            FROM police
            GROUP BY country_name
            ORDER BY searches DESC
            LIMIT 1;
        """,
        sql_questions[14]: """
            SELECT strftime('%Y', timestamp) AS year, country_name,
                   COUNT(*) AS stops,
                   SUM(CASE WHEN is_arrested THEN 1 ELSE 0 END) AS arrests
            FROM police
            GROUP BY year, country_name
            ORDER BY year, arrests DESC;
        """,
        sql_questions[15]: """
            SELECT driver_race, driver_age, violation, COUNT(*) AS count
            FROM police
            GROUP BY driver_race, driver_age, violation
            ORDER BY count DESC;
        """,
        sql_questions[16]: """
            SELECT 
            strftime('%Y', timestamp) AS year,
            strftime('%m', timestamp) AS month,
            strftime('%H', timestamp) AS hour,
            strftime('%H', timestamp) || ':00 to ' || strftime('%H', timestamp) || ':59' AS time_range,
            COUNT(*) AS count
            FROM police
            GROUP BY year, month, hour
            ORDER BY year, month, hour;
        """,
        sql_questions[17]: """
            SELECT 
            violation,
            ROUND((SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) * 100, 2) AS arrest_rate,
            ROUND((SUM(CASE WHEN search_conducted = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*)) * 100, 2) AS search_rate
            FROM police
            GROUP BY violation
            ORDER BY arrest_rate DESC, search_rate DESC
            LIMIT 10;
        """,
        sql_questions[18]: """
            SELECT country_name, driver_gender, AVG(driver_age) AS avg_age
            FROM police
            WHERE driver_age IS NOT NULL
            GROUP BY country_name, driver_gender;
        """,
        sql_questions[19]: """
            SELECT violation,
                   ROUND(SUM(CASE WHEN is_arrested = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(), 2) AS arrest_rate
            FROM police
            GROUP BY violation
            ORDER BY arrest_rate DESC
            LIMIT 5;
        """
    }

    if "selected_question" not in st.session_state:
        st.session_state.selected_question = sql_questions[0]

    selected_question = st.selectbox(
        "Select a Question", 
        sql_questions, 
        index=sql_questions.index(st.session_state.selected_question)
    )

    if selected_question != st.session_state.selected_question:
        st.session_state.selected_question = selected_question
        st.session_state.query_result = None

    if st.button("Run Query"):
        if selected_question in sql_queries:
            try:
                query = sql_queries[selected_question]
                st.session_state.query_result = pd.read_sql(query, conn)
            except Exception as e:
                st.error(f"❌ Error running query: {e}")
                st.session_state.query_result = None

    if st.session_state.get("query_result") is not None:
        if len(st.session_state.query_result) > 0:
            st.dataframe(st.session_state.query_result)
        else:
            st.info("No results found for the selected query.")
