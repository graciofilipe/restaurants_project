import streamlit as st
import pandas as pd
from google.cloud import bigquery
from google.api_core.exceptions import NotFound, Forbidden

def display_bq_table():
    st.title("BigQuery Table Viewer")

    bq_uri = st.text_input("Enter BigQuery Table URI (e.g., project_id.dataset_id.table_id)", "")
    load_button = st.button("Load Table")

    if load_button and bq_uri:
        try:
            if len(bq_uri.split('.')) != 3:
                st.error("Invalid BigQuery URI format. Please use 'project_id.dataset_id.table_id'")
                return

            client = bigquery.Client()
            table_ref = client.get_table(bq_uri) # Try to get table to check existence and basic permissions

            st.info(f"Fetching table: {bq_uri}")
            
            # Construct the query
            query = f"SELECT * FROM `{bq_uri}`" # Use backticks for safety with special characters in names
            
            # Execute the query
            query_job = client.query(query)
            
            # Convert to Pandas DataFrame
            df = query_job.to_dataframe()
            
            st.success(f"Successfully loaded table: {bq_uri}")
            st.dataframe(df)

        except Forbidden:
            st.error(f"Permission denied for table: {bq_uri}. Ensure you have the necessary BigQuery permissions (e.g., BigQuery Data Viewer role).")
        except NotFound:
            st.error(f"Table not found: {bq_uri}. Please check the Project ID, Dataset ID, and Table ID.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    elif load_button and not bq_uri:
        st.warning("Please enter a BigQuery Table URI.")

if __name__ == "__main__":
    # This allows the page to be run independently for testing if needed,
    # though it will primarily be imported and called by streamlit_app.py
    display_bq_table()
