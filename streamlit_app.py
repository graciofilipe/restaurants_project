import streamlit as st
import pandas as pd
import os
import sys

try:
    from restaurant_finder.main import find_restaurants_in_batches
except ImportError as e:
    st.error(f"Error importing find_restaurants_in_batches: {e}. Ensure restaurant_finder module is accessible.")
    # You might want to stop the app here or provide more specific instructions
    # For now, we'll let it potentially fail later if the import didn't work.

def main():
    st.title("Restaurant Finder")

    # --- UI Elements ---
    st.header("Configuration")

    project_id_input = st.text_input("Google Cloud Project ID", 
                                     help="Your GCP Project ID is required for backend operations (GCS, BigQuery, Maps API).")

    uploaded_file = st.file_uploader("Upload a CSV file with columns: 'latitude', 'longitude', and optionally 'radius' (in km)",
                                     type="csv")

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

        if uploaded_file is None:
            st.error("Please upload a CSV file with coordinates.")
            st.stop()

        # Set Project ID environment variable
        # This is crucial if any backend function (or its auxiliaries) relies on os.environ.get('PROJECT_ID')
        os.environ['PROJECT_ID'] = project_id_input
        st.info(f"PROJECT_ID environment variable set to: {project_id_input}")


        try:
            df = pd.read_csv(uploaded_file)

            if 'latitude' not in df.columns or 'longitude' not in df.columns:
                st.error("CSV must contain 'latitude' and 'longitude' columns.")
                st.stop()

            latlong_list_input = []
            default_radius_meters = int(default_radius_for_input_km * 1000) # Use renamed variable

            for _, row in df.iterrows():
                lat = row['latitude']
                lon = row['longitude']
                # Radius: use from CSV if present (and assume it's in km), else use default
                # The backend expects radius in meters for each point in the list.
                if 'radius' in df.columns and pd.notna(row['radius']):
                    radius_for_point_meters = int(float(row['radius']) * 1000) 
                else:
                    radius_for_point_meters = default_radius_meters
                # Backend expects radius_for_point_meters in meters
                latlong_list_input.append((lat, lon, radius_for_point_meters))
            
            if not latlong_list_input:
                st.error("No valid coordinates found in the CSV or CSV is empty.")
                st.stop()

            st.info(f"Prepared {len(latlong_list_input)} coordinates for processing.")
            
            # Call Backend Function
            st.info("Finding restaurants... This may take a few minutes.")
            with st.spinner('Processing...'):
                # The 'radius_input' to find_restaurants_in_batches is the general default radius (like args.radius),
                # but the individual radii in latlong_list_input will be used by iterate_over_calls.
                # We pass default_radius_meters for this parameter.
                restaurants_dict = find_restaurants_in_batches(
                    latlong_list_input=latlong_list_input,
                    project_id_input=project_id_input,
                    radius_input=default_radius_meters, # General default radius in meters
                    limit_input=int(limit_coords),
                    amount_of_noise_input=float(amount_of_noise),
                    spoke_generation_radius_meters=int(spoke_radius_input) # Pass the new spoke radius
                )

            # Display Results
            if restaurants_dict:
                st.success(f"Found {len(restaurants_dict)} unique restaurants!")
                results_df = pd.DataFrame.from_dict(restaurants_dict, orient='index')
                
                # Define columns to display, checking if they exist
                display_cols = []
                potential_cols = ['displayName', 'shortFormattedAddress', 'rating', 'priceLevel', 'primary_type', 'user_rating_count', 'location']
                for col in potential_cols:
                    if col in results_df.columns:
                        display_cols.append(col)
                
                if 'displayName' in results_df.columns: # Check if primary key column exists
                     st.dataframe(results_df[display_cols])


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

        except ImportError: # Catches the import error if it wasn't caught at the top
            st.error("Critical Error: The backend function 'find_restaurants_in_batches' could not be imported. Please check the server logs.")
        except FileNotFoundError as e:
            st.error(f"File not found: {e}. This might be related to the CSV path or backend file access.")
        except pd.errors.EmptyDataError:
            st.error("The uploaded CSV file is empty.")
        except pd.errors.ParserError:
            st.error("Could not parse the CSV file. Please ensure it's a valid CSV.")
        except ValueError as ve:
            st.error(f"Input error: {ve}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
            st.error("Details: " + str(e)) # provide more details for debugging

if __name__ == "__main__":
    # Check if find_restaurants_in_batches was imported successfully before running
    if 'find_restaurants_in_batches' in globals():
        main()
    else:
        st.error("Application cannot start because the backend function failed to import.")
    st.info("This usually means the `restaurant_finder.main` module was not found. "
                "Ensure the Streamlit app is launched from a context where this module is in the Python path, "
                "or that the path adjustments in `app.py` are correct.")
