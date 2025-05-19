import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime

try:
    from restaurant_finder.main import find_restaurants_in_batches
    from restaurant_finder.aux_functions import get_latlong_from_bucket
except ImportError as e:
    st.error(f"Error importing find_restaurants_in_batches or get_latlong_from_bucket: {e}. Ensure restaurant_finder module and its dependencies are accessible.")
    # You might want to stop the app here or provide more specific instructions
    # For now, we'll let it potentially fail later if the import didn't work.

# Import for BigQuery Table Viewer
from .bq_table_viewer import display_bq_table

def restaurant_finder_app(): # Renamed from main
    st.title("Restaurant Finder")

    # --- UI Elements ---
    st.header("Configuration")

    project_id_input = st.text_input("Google Cloud Project ID", 
                                     help="Your GCP Project ID is required for backend operations (GCS, BigQuery, Maps API).")

    gcs_path_input = st.text_input("GCS Path for Coordinates CSV",
                                   help="Enter the GCS path to your CSV file, like `gs://your-bucket-name/path/to/your-file.csv`")

    default_radius_for_input_km = st.number_input("Default Search Radius (km)",
                                                  min_value=0.1, value=1.0, step=0.1,
                                                  help="Enter radius in kilometers. This will be converted to meters for the backend processing.")
    
    limit_coords = st.number_input("Limit number of coordinates to process",
                                   min_value=1, value=10, step=1,
                                   help="Maximum number of coordinates to process from the uploaded file.")
    
    amount_of_noise = st.number_input("Amount of Noise (for coordinates)",
                                      min_value=0.0, value=0.002, step=0.0001, format="%.4f",
                                      help="Noise added to coordinates for broader search, if needed by the backend.")

    spoke_radius_input = st.number_input("Spoke Generation Radius (meters)",
                                         min_value=10, value=100, step=10,
                                         help="Radius in meters for generating additional search points around saturated areas.")

    if st.button("Find Restaurants"):
        # --- Processing Logic ---
        if not project_id_input:
            st.error("Please enter the Google Cloud Project ID.")
            st.stop()

        if not gcs_path_input:
            st.error("Please enter the GCS path for the coordinates CSV file.")
            st.stop()

        # Set Project ID environment variable
        # This is crucial if any backend function (or its auxiliaries) relies on os.environ.get('PROJECT_ID')
        os.environ['PROJECT_ID'] = project_id_input
        st.info(f"PROJECT_ID environment variable set to: {project_id_input}")


        try:
            default_radius_meters = int(default_radius_for_input_km * 1000)
            latlong_list_input = [] # Initialize to ensure it's defined

            if not gcs_path_input.startswith("gs://"):
                st.error("Invalid GCS path format. Must start with 'gs://'.")
                st.stop()

            parts = gcs_path_input[5:].split("/", 1)
            if len(parts) < 2 or not parts[0] or not parts[1]: # Check for bucket and file path
                st.error("Invalid GCS path format. Must include bucket name and file path (e.g., gs://bucket/file.csv).")
                st.stop()
            
            bucket_name = parts[0]
            file_path_in_bucket = parts[1]

            st.info(f"Attempting to read from GCS bucket: '{bucket_name}', file: '{file_path_in_bucket}'")

            # Call get_latlong_from_bucket
            # Parameters: project_id, bucket_name, latlong_list (file path in bucket), latlong_resolution, radius
            latlong_list_input = get_latlong_from_bucket(
                project_id=project_id_input,
                bucket_name=bucket_name,
                latlong_list=file_path_in_bucket, # This is file_path_in_bucket
                latlong_resolution=2, # Default value as specified
                radius=default_radius_meters # Default radius in meters
            )

            if not latlong_list_input:
                st.error("No valid coordinates found in the GCS file, or the file is empty.")
                st.stop()

            st.info(f"Prepared {len(latlong_list_input)} coordinates for processing.")
            
            # Call Backend Function
            st.info("Finding restaurants... This may take a few minutes.")
            with st.spinner('Processing...'):
                restaurants_dict = find_restaurants_in_batches(
                    latlong_list_input=latlong_list_input,
                    project_id_input=project_id_input,
                    radius_input=default_radius_meters, 
                    limit_input=int(limit_coords),
                    amount_of_noise_input=float(amount_of_noise),
                    spoke_generation_radius_meters=int(spoke_radius_input)
                )

            today_str = datetime.today().strftime('%Y-%m-%d')

            # Display Results
            if restaurants_dict:
                st.success(f"Found {len(restaurants_dict)} unique restaurants!")
                results_df = pd.DataFrame.from_dict(restaurants_dict, orient='index')

                # Date filtering logic
                if 'first_seen' in results_df.columns:
                    st.write(f"Filtering for 'first_seen' date: {today_str}")
                    try:
                        # Convert to datetime, coercing errors to NaT
                        dt_series = pd.to_datetime(results_df['first_seen'], errors='coerce')
                        # Format to string 'YYYY-MM-DD'; NaT will become 'NaT' (a string) or stay pd.NaT depending on pandas version
                        results_df['first_seen'] = dt_series.dt.strftime('%Y-%m-%d')
                        
                        # Ensure everything is a string. Replace 'NaT' strings or any non-string (like actual pd.NaT if strftime didn't convert it) with empty string.
                        # A robust way to check for pd.NaT if it wasn't converted to string 'NaT' by strftime:
                        # results_df['first_seen'] = results_df['first_seen'].apply(lambda x: '' if pd.isna(x) else x)
                        # Then, ensure all are strings, especially if 'NaT' strings are present.
                        results_df['first_seen'] = results_df['first_seen'].astype(str)
                        # Replace string 'NaT' (if NaT was converted to this string by strftime or astype) with empty string
                        results_df['first_seen'] = results_df['first_seen'].replace('NaT', '')

                    except Exception as e:
                        st.warning(f"Error during 'first_seen' column processing: {e}. Attempting to proceed, but date filtering may be affected.")
                        # As a fallback, ensure the column is string type to prevent subsequent errors, filling errors with empty string
                        results_df['first_seen'] = results_df['first_seen'].astype(str).fillna('')

                    # Now, the column should be all strings (either 'YYYY-MM-DD' or '')
                    # The original check 'is_string_dtype' might be too strict if mixed (e.g. actual NaT objects),
                    # but after the above conversions, it should be safer.
                    # However, direct comparison should work fine now.
                    
                    # Proceed with filtering
                    filtered_df = results_df[results_df['first_seen'] == today_str]
                    if not filtered_df.empty or results_df['first_seen'].eq(today_str).any():
                        results_df = filtered_df
                    elif not results_df['first_seen'].eq('').all(): # Only warn if there were actual dates that didn't match
                        st.info(f"No entries found for 'first_seen' date: {today_str}. Displaying all entries.")
                    # No explicit warning if all were empty strings (i.e. invalid dates)

                else:
                    st.warning("Warning: 'first_seen' column not found in results. Cannot apply date filter.")

                # Define columns to display, checking if they exist
                display_cols = []
                potential_cols = ['displayName', 'shortFormattedAddress', 'rating', 'priceLevel', 'primary_type', 'user_rating_count', 'location']
                for col in potential_cols:
                    if col in results_df.columns:
                        display_cols.append(col)
                
                if 'displayName' in results_df.columns: # Check if primary key column exists
                     st.dataframe(results_df[display_cols])
                else:
                    st.info("No 'displayName' column in results, cannot display table.")


                # Optional Map Display:
                # The Places API response includes geometry.location.lat and geometry.location.lng
                # Assuming 'location' column might be a dict {'lat': ..., 'lng': ...} or similar
                # Or that iterate_over_calls was modified to return flat lat/lng.
                # For now, let's assume 'latitude' and 'longitude' columns are added by the backend if possible,
                # or we extract them if they are nested.
                
                # Attempt to extract lat/lng if 'location' column with dicts exists
                if 'location' in results_df.columns and not results_df.empty and isinstance(results_df['location'].iloc[0], dict):
                    try:
                        results_df['latitude'] = results_df['location'].apply(lambda loc: loc.get('lat') if isinstance(loc, dict) else None)
                        results_df['longitude'] = results_df['location'].apply(lambda loc: loc.get('lng') if isinstance(loc, dict) else None)
                        # Drop rows where lat/lng extraction failed
                        map_df = results_df.dropna(subset=['latitude', 'longitude'])
                        if not map_df.empty:
                           st.map(map_df[['latitude', 'longitude']])
                        else:
                           st.info("Could not extract latitude/longitude from 'location' data for map display.")
                    except Exception as e:
                        st.warning(f"Could not process 'location' data for map display: {e}")

                elif 'latitude' in results_df.columns and 'longitude' in results_df.columns:
                     st.map(results_df[['latitude', 'longitude']].dropna())
                else:
                    st.info("Map display skipped: 'latitude'/'longitude' columns not found or 'location' field not in expected format.")

            else:
                st.info("No restaurants found for the given locations.")

        except ImportError: 
            st.error("Critical Error: A required backend function ('find_restaurants_in_batches' or 'get_latlong_from_bucket') could not be imported. Please check server logs and ensure the 'restaurant_finder' module is correctly installed and accessible.")
        except ValueError as ve: # Catch specific ValueErrors from path parsing or function calls
            st.error(f"Configuration or Input Error: {ve}")
        except FileNotFoundError as fnfe: # If get_latlong_from_bucket raises this for GCS
            st.error(f"GCS File Error: {fnfe}. Ensure the file exists at the specified path and the application has permissions.")
        except pd.errors.EmptyDataError: 
            st.error("The CSV file from GCS is empty or contains no data.")
        except pd.errors.ParserError: 
            st.error("Could not parse the CSV file from GCS. Please ensure it's a valid CSV with expected columns ('LAT', 'LONG', optionally 'RADIUS_KM').")
        except Exception as e: # General catch-all for other unexpected errors
            st.error(f"An unexpected error occurred during GCS processing or restaurant finding: {e}")
            st.error("Details: " + str(e))

if __name__ == "__main__":
    # Check if find_restaurants_in_batches was imported successfully before running
    if 'find_restaurants_in_batches' in globals():
        main()
    else:
        st.error("Application cannot start because the backend function failed to import.")
    st.info("This usually means the `restaurant_finder.main` module was not found. "
                "Ensure the Streamlit app is launched from a context where this module is in the Python path, "
                "or that the path adjustments in `app.py` are correct.")

def main():
    st.sidebar.title("Navigation")
    app_choice = st.sidebar.radio("Choose App", ["Restaurant Finder", "BigQuery Table Viewer"])

    if app_choice == "Restaurant Finder":
        # Check if find_restaurants_in_batches was imported successfully before running restaurant_finder_app
        if 'find_restaurants_in_batches' in globals() and 'get_latlong_from_bucket' in globals():
            restaurant_finder_app()
        else:
            st.error("Restaurant Finder app cannot start because a backend function failed to import. "
                     "This usually means the `restaurant_finder.main` module was not found or there's an issue with its dependencies.")
            st.info("Ensure the Streamlit app is launched from a context where this module is in the Python path.")
            # Optionally, you could display a message or part of the UI that doesn't depend on these imports
    elif app_choice == "BigQuery Table Viewer":
        display_bq_table()

if __name__ == "__main__":
    main() # Call the new main function
