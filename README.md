# Policelogs
Step 1: Load Raw Data
  Opened the Visual Studio Code
  Loaded the raw file traffic_stops_with_vehicle_number_raw_data.csv.
Step 2: Data Cleaning and Processing
   Combined stop_date and stop_time columns into a single timestamp column.
   Removed unwanted Columns 
   *stop_date
   *stop_time
   *driver_age_raw
Step 3: Save Cleaned Data
    Saved the cleaned data to a new CSV file named traffic_stops_cleaned_important54.csv.
Step 4: Store Data in Database
    Created a SQLite database called traffic_stops.db.
    Stored the cleaned data into a table named police.
Step 5: Create Streamlit App
    Started a new Python file for the dashboard (like app.py).
    Set up the Streamlit page configuration.
Step 6: Add Navigation Menu
    Added a horizontal menu with sections like:
    Home
    Generate Summary
    SQL Query Explorer
Step 7: Home Page
    Loaded data from the database.
    Displayed key metrics like:
    *Total police stops
    *Total Arrests
    *Total Warnings
Step 8: Generate Summary Page
    Took user input (date, time, driver details).
    Filtered matching records.
    Displayed a summary if a match was found.
    Showed warnings for incomplete or incorrect inputs.
Step 9: SQL Query Explorer Page
    Provided a dropdown of 20 predefined traffic analysis questions.
    Ran the corresponding SQL query based on selection.
    Displayed the results in a table.
