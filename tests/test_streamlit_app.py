import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd # Required for type hints and mocking if df operations are involved
from datetime import datetime, date # Added for the new test

# Add the parent directory to sys.path to allow importing streamlit_app
# This is often needed when tests are in a subdirectory.
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now try to import the module to be tested
try:
    import streamlit_app
except ModuleNotFoundError:
    # This can happen if streamlit_app.py itself has import errors not related to its own path
    # For example, if restaurant_finder is not found from the root directory.
    # The sys.path.insert above should handle streamlit_app.py being found.
    print("Failed to import streamlit_app. Check its internal imports and project structure.")
    raise

# Define a dummy DataFrame to be returned by mocked functions if needed
dummy_df = pd.DataFrame({'col1': [1, 2], 'col2': ['A', 'B']})
dummy_restaurants_dict = {
    'restaurant1': {'displayName': 'Test Cafe', 'shortFormattedAddress': '123 Test St', 'rating': 4.5}
}
dummy_lat_long_list = [(10.0, 20.0, 500), (30.0, 40.0, 1000)]


class TestStreamlitAppGCSProcessing(unittest.TestCase):

    @patch('streamlit_app.st')
    @patch('streamlit_app.get_latlong_from_bucket')
    @patch('streamlit_app.find_restaurants_in_batches')
    @patch('streamlit_app.pd.DataFrame.from_dict') # If results are processed
    def test_successful_gcs_path_processing(self, mock_from_dict, mock_find_restaurants, mock_get_latlong, mock_st):
        # --- Setup Mocks ---
        # Simulate UI inputs
        # The order of side_effect values should match the order of st.text_input/st.number_input calls in streamlit_app.py
        mock_st.text_input.side_effect = [
            "test-project-id",  # project_id_input
            "gs://test-bucket/data/coords.csv"  # gcs_path_input
        ]
        mock_st.number_input.side_effect = [
            1.0,  # default_radius_for_input_km (1.0 km = 1000 m)
            10,   # limit_coords
            0.002,# amount_of_noise
            100   # spoke_radius_input
        ]
        mock_st.button.return_value = True # Simulate button click

        # Mock external function calls
        mock_get_latlong.return_value = dummy_lat_long_list
        mock_find_restaurants.return_value = dummy_restaurants_dict
        mock_from_dict.return_value = dummy_df # If DataFrame conversion happens

        # Mock spinner to act as a context manager
        mock_spinner_instance = MagicMock()
        mock_st.spinner.return_value = mock_spinner_instance
        mock_spinner_instance.__enter__.return_value = None
        mock_spinner_instance.__exit__.return_value = None
        
        # --- Execute ---
        streamlit_app.main()

        # --- Assertions ---
        # 1. Assert get_latlong_from_bucket was called correctly
        expected_radius_meters = 1.0 * 1000
        mock_get_latlong.assert_called_once_with(
            project_id="test-project-id",
            bucket_name="test-bucket",
            latlong_list="data/coords.csv", # This is the file_path_in_bucket
            latlong_resolution=2,
            radius=expected_radius_meters
        )

        # 2. Assert find_restaurants_in_batches was called with the result
        mock_find_restaurants.assert_called_once_with(
            latlong_list_input=dummy_lat_long_list,
            project_id_input="test-project-id",
            radius_input=expected_radius_meters,
            limit_input=10,
            amount_of_noise_input=0.002,
            spoke_generation_radius_meters=100
        )

        # 3. Assert that no st.error was called
        mock_st.error.assert_not_called()
        mock_st.stop.assert_not_called() # Ensure processing wasn't prematurely stopped

        # 4. Assert UI feedback (optional, but good for completeness)
        self.assertIn(call.info("PROJECT_ID environment variable set to: test-project-id"), mock_st.method_calls)
        self.assertIn(call.info("Attempting to read from GCS bucket: 'test-bucket', file: 'data/coords.csv'"), mock_st.method_calls)
        self.assertIn(call.info(f"Prepared {len(dummy_lat_long_list)} coordinates for processing."), mock_st.method_calls)
        self.assertIn(call.info("Finding restaurants... This may take a few minutes."), mock_st.method_calls)
        self.assertIn(call.success(f"Found {len(dummy_restaurants_dict)} unique restaurants!"), mock_st.method_calls)


    @patch('streamlit_app.st')
    @patch('streamlit_app.get_latlong_from_bucket')
    @patch('streamlit_app.find_restaurants_in_batches')
    def test_invalid_gcs_path_no_prefix(self, mock_find_restaurants, mock_get_latlong, mock_st):
        # --- Setup Mocks ---
        mock_st.text_input.side_effect = [
            "test-project-id",
            "invalid-path/data.csv"  # Invalid GCS path
        ]
        mock_st.number_input.side_effect = [1.0, 10, 0.002, 100] # Values don't matter much here
        mock_st.button.return_value = True

        # --- Execute ---
        streamlit_app.main()

        # --- Assertions ---
        mock_st.error.assert_called_once_with("Invalid GCS path format. Must start with 'gs://'.")
        mock_st.stop.assert_called_once()
        mock_get_latlong.assert_not_called()
        mock_find_restaurants.assert_not_called()

    @patch('streamlit_app.st')
    @patch('streamlit_app.get_latlong_from_bucket')
    @patch('streamlit_app.find_restaurants_in_batches')
    def test_invalid_gcs_path_incomplete(self, mock_find_restaurants, mock_get_latlong, mock_st):
        # --- Setup Mocks ---
        mock_st.text_input.side_effect = [
            "test-project-id",
            "gs://test-bucket"  # Incomplete GCS path (missing file)
        ]
        mock_st.number_input.side_effect = [1.0, 10, 0.002, 100]
        mock_st.button.return_value = True

        # --- Execute ---
        streamlit_app.main()

        # --- Assertions ---
        mock_st.error.assert_called_once_with("Invalid GCS path format. Must include bucket name and file path (e.g., gs://bucket/file.csv).")
        mock_st.stop.assert_called_once()
        mock_get_latlong.assert_not_called()
        mock_find_restaurants.assert_not_called()

    @patch('streamlit_app.st')
    @patch('streamlit_app.get_latlong_from_bucket')
    @patch('streamlit_app.find_restaurants_in_batches')
    def test_gcs_read_fails_empty_list_returned(self, mock_find_restaurants, mock_get_latlong, mock_st):
        # --- Setup Mocks ---
        mock_st.text_input.side_effect = [
            "test-project-id",
            "gs://test-bucket/data/empty.csv"
        ]
        mock_st.number_input.side_effect = [1.0, 10, 0.002, 100]
        mock_st.button.return_value = True
        
        mock_get_latlong.return_value = [] # Simulate GCS returning no valid coordinates

        # --- Execute ---
        streamlit_app.main()

        # --- Assertions ---
        mock_get_latlong.assert_called_once() # Should still be called
        mock_st.error.assert_called_once_with("No valid coordinates found in the GCS file, or the file is empty.")
        mock_st.stop.assert_called_once()
        mock_find_restaurants.assert_not_called()

    @patch('streamlit_app.st')
    @patch('streamlit_app.get_latlong_from_bucket')
    @patch('streamlit_app.find_restaurants_in_batches')
    def test_project_id_missing(self, mock_find_restaurants, mock_get_latlong, mock_st):
        # --- Setup Mocks ---
        mock_st.text_input.side_effect = [
            "",  # Empty project_id_input
            "gs://test-bucket/data/coords.csv" 
        ]
        mock_st.number_input.side_effect = [1.0, 10, 0.002, 100]
        mock_st.button.return_value = True

        # --- Execute ---
        streamlit_app.main()

        # --- Assertions ---
        mock_st.error.assert_called_once_with("Please enter the Google Cloud Project ID.")
        mock_st.stop.assert_called_once()
        mock_get_latlong.assert_not_called()
        mock_find_restaurants.assert_not_called()

    @patch('streamlit_app.st')
    @patch('streamlit_app.get_latlong_from_bucket') # Still need to mock it even if not called
    @patch('streamlit_app.find_restaurants_in_batches')
    def test_gcs_path_missing(self, mock_find_restaurants, mock_get_latlong, mock_st):
        # --- Setup Mocks ---
        mock_st.text_input.side_effect = [
            "test-project-id", 
            ""  # Empty gcs_path_input
        ]
        mock_st.number_input.side_effect = [1.0, 10, 0.002, 100]
        mock_st.button.return_value = True

        # --- Execute ---
        streamlit_app.main()

        # --- Assertions ---
        mock_st.error.assert_called_once_with("Please enter the GCS path for the coordinates CSV file.")
        mock_st.stop.assert_called_once()
        mock_get_latlong.assert_not_called()
        mock_find_restaurants.assert_not_called()

    @patch('streamlit_app.st')
    @patch('streamlit_app.get_latlong_from_bucket') # Mocked as it's part of the flow before filtering
    @patch('streamlit_app.find_restaurants_in_batches')
    @patch('streamlit_app.datetime')
    def test_filter_restaurants_by_first_seen_date_correct(self, mock_dt, mock_find_restaurants, mock_get_latlong, mock_st):
        # --- Setup Mocks ---
        mock_today = date(2025, 5, 19)
        
        # Configure datetime mock
        mock_dt.today.return_value = mock_today
        # strftime is called on the date object returned by today()
        # So, we make sure today() returns an object that has a strftime method
        # No need to mock strftime separately if today() returns a real date object, 
        # or a mock that behaves like one.
        # If datetime.today() is called directly and then strftime, then:
        # mock_dt.today.return_value.strftime.return_value = mock_today.strftime('%Y-%m-%d')

        sample_restaurants_data = {
            "id1": {"displayName": "Restaurant A", "first_seen": "2025-05-19", "location": {"lat":1, "lng":1}},
            "id2": {"displayName": "Restaurant B", "first_seen": "2025-05-18", "location": {"lat":1, "lng":1}},
            "id3": {"displayName": "Restaurant C", "first_seen": "2025-05-19", "location": {"lat":1, "lng":1}},
            "id4": {"displayName": "Restaurant D", "location": {"lat":1, "lng":1}}, # No first_seen
            "id5": {"displayName": "Restaurant E", "first_seen": "2024-01-01", "location": {"lat":1, "lng":1}},
            # Test with actual date object, app should convert it
            "id6": {"displayName": "Restaurant F", "first_seen": date(2025, 5, 19), "location": {"lat":1, "lng":1}}, 
        }
        mock_find_restaurants.return_value = sample_restaurants_data

        # Simulate UI inputs necessary to reach the relevant part of the code
        mock_st.text_input.side_effect = [
            "test-project-id",  # project_id_input
            "gs://test-bucket/data/coords.csv"  # gcs_path_input
        ]
        mock_st.number_input.side_effect = [
            1.0,  # default_radius_for_input_km
            10,   # limit_coords
            0.002,# amount_of_noise
            100   # spoke_radius_input
        ]
        mock_st.button.return_value = True # Simulate button click

        # Mock get_latlong_from_bucket to return some dummy data
        mock_get_latlong.return_value = [(10.0, 20.0, 500)] # Dummy coordinate list

        # Mock spinner to act as a context manager
        mock_spinner_instance = MagicMock()
        mock_st.spinner.return_value = mock_spinner_instance
        mock_spinner_instance.__enter__.return_value = None
        mock_spinner_instance.__exit__.return_value = None

        # --- Execute ---
        streamlit_app.main()

        # --- Assertions ---
        # Check that st.dataframe was called
        mock_st.dataframe.assert_called() # Check if it was called at least once

        # Capture the DataFrame passed to st.dataframe
        # The actual call might be mock_st.dataframe(results_df[display_cols])
        # We need to get the first argument of the last call to st.dataframe
        call_args = mock_st.dataframe.call_args
        self.assertIsNotNone(call_args, "st.dataframe was not called")
        
        displayed_df = call_args[0][0] # Get the first positional argument of the call

        # Perform assertions on the displayed_df
        self.assertEqual(len(displayed_df), 3, f"Expected 3 rows, got {len(displayed_df)}")
        self.assertIn("id1", displayed_df.index)
        self.assertIn("id3", displayed_df.index)
        self.assertIn("id6", displayed_df.index) # This should be included as its date matches mock_today
        
        self.assertNotIn("id2", displayed_df.index)
        self.assertNotIn("id4", displayed_df.index) # No 'first_seen'
        self.assertNotIn("id5", displayed_df.index)

        # Verify that the warning for 'first_seen' not found was NOT called for id4 (it is handled)
        # but that the general processing continued.
        # We expect a warning for 'first_seen' column not found if the *column itself* is missing,
        # not for individual rows. The current code applies a warning if the column is missing entirely.
        # If 'id4' caused a specific warning that we want to check, the app logic would need to do that.
        # The current test setup implies the column 'first_seen' WILL exist due to other entries.
        
        # Check that st.write was called with the filtering message
        mock_st.write.assert_any_call(f"Filtering for 'first_seen' date: {mock_today.strftime('%Y-%m-%d')}")


if __name__ == '__main__':
    unittest.main()
