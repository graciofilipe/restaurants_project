scrappy code to indetify local restaurants and compare them against a previous list. The goal is to find new restaurants that weren't there before. 


## Arguments for Restaurant Finder Script

This script takes the following arguments:

*   **`--radius`**:  This argument defines the radius (in meters) around each point in the latitude/longitude grid within which to search for restaurants.  The default value is 666 meters.  Increasing the radius expands the search area, potentially finding more restaurants but also increasing the likelihood of hitting the API limit.  Decreasing the radius narrows the search area.

*   **`--latlong_list`**: This argument specifies the path to the CSV file in Cloud Storage containing the latitude/longitude pairs that define the search grid. This file should contain columns named `LAT` and `LONG` representing the coordinates.  The default value is "postcodes/latlong.csv".

*   **`--limit`**:  This argument sets a limit on the number of latitude/longitude pairs to process from the input CSV.  This is useful for testing or when dealing with large datasets. If the number of points in the  `latlong_list` exceeds this limit, a random sample of points will be selected for processing.  The default value is 20.

*   **`--amount_of_noise`**:  This argument introduces random noise to the latitude and longitude coordinates. The noise is drawn from a normal distribution with a mean of 0 and a standard deviation equal to this argument's value.  This helps prevent redundant API calls when points in the grid are very close together and can distribute the search more evenly.  The default value is 0.002.

*   **`--latlong_resolution`**: This argument controls the precision of the latitude and longitude coordinates by rounding them to the specified number of decimal places. For example, a value of 3 would round coordinates to three decimal places (e.g., 34.123, -118.456).  This helps to reduce the number of unique locations and consolidate nearby searches. The default value is 3.


 - example prompt: Select the name, rating, user_rating_count, and types for the restaurants that have first_seen less than 60 days from today and have user_rating_count between 5 and 60. Order by average rating descending

SELECT
  displayName,
  rating as average_rating,
  user_rating_count as number_of_reviews, 
  shortFormattedAddress, 
  primary_type,
  types as extra_types
FROM
  `project-name.restaurants_dataset.restaurants_table`
WHERE
  DATE_DIFF(CURRENT_DATE(), first_seen, DAY) < 30
  AND user_rating_count BETWEEN 5 AND 66
  AND rating > 4
ORDER BY
  rating DESC;

## Streamlit Frontend for Restaurant Finder

This Streamlit application provides a user interface for the Restaurant Finder. You can upload a CSV file containing geolocations (latitude, longitude, and an optional radius in km per point) to find restaurants in those areas.

### Prerequisites

*   Python 3.10 or higher.
*   Google Cloud Project ID with Billing enabled.
*   Enabled APIs: Places API (part of Maps SDK), Cloud Storage, BigQuery API.
*   Authenticated `gcloud` CLI or Application Default Credentials set up with permissions to access Google Cloud services (Storage, BigQuery, Secret Manager for the Maps API key).
*   The backend expects the Maps API key to be stored in Secret Manager with the name 'maps-key'. (The `run_restaurant_finder/maps_call.py` script handles fetching this key).

### Setup & Running Locally

1.  **Clone the repository.**
2.  **Navigate to the repository root.**
3.  **Install backend dependencies:**
    ```bash
    pip install -r run_restaurant_finder/requirements.txt
    ```
4.  **Install frontend dependencies:**
    ```bash
    pip install -r frontend_streamlit/requirements.txt
    ```
5.  **Set the `PROJECT_ID` environment variable:**
    *   On Linux/macOS:
        ```bash
        export PROJECT_ID="your-gcp-project-id"
        ```
    *   On Windows (Command Prompt):
        ```cmd
        set PROJECT_ID=your-gcp-project-id
        ```
    *   On Windows (PowerShell):
        ```powershell
        $env:PROJECT_ID="your-gcp-project-id"
        ```
    *   *Alternatively, the application will prompt you to enter the Project ID in the UI if this environment variable is not set.*
6.  **Run the Streamlit application:**
    ```bash
    streamlit run frontend_streamlit/app.py
    ```
7.  Open your browser and navigate to the local URL provided by Streamlit (usually `http://localhost:8501`).

### Input CSV Format

*   The CSV file **must** contain 'latitude' and 'longitude' columns.
*   An optional 'radius' column can be included, specifying the search radius in **kilometers** for each specific point. If this column is absent or a value is missing for a row, the default radius (in km) entered in the UI will be used for that point.

### Docker Deployment (Optional)

A `Dockerfile` is provided in the `frontend_streamlit` directory to build a container image for the application. This Dockerfile copies both frontend and backend code and installs their respective dependencies.

1.  **Build the Docker image** (from the repository root):
    ```bash
    docker build -t restaurant-finder-frontend -f frontend_streamlit/Dockerfile .
    ```
2.  **Run the Docker container:**
    ```bash
    docker run -p 8501:8501 -e PROJECT_ID="your-gcp-project-id" restaurant-finder-frontend
    ```
    *   **Note on GCP Authentication**: Ensure the container can access GCP credentials. This can be achieved by:
        *   Mounting your local `gcloud` configuration directory (e.g., `~/.config/gcloud`) into the container.
        *   Using a service account key file (mount the file and set `GOOGLE_APPLICATION_CREDENTIALS`).
        *   Using Workload Identity Federation if deploying to Google Cloud (e.g., Cloud Run, GKE).
    *   The `PROJECT_ID` environment variable must be passed to the container as shown above.
