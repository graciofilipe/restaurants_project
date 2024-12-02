from google.cloud import secretmanager
from google.cloud import storage
import numpy as np
import pandas as pd



def build_lat_long_grid(top_left, bottom_right, n_steps, radius):

    lat_step = (top_left[0] - bottom_right[0]) / n_steps
    long_step = (bottom_right[1] - top_left[1]) / n_steps
    lat_long_pairs = []
    for i in range(n_steps):
        for j in range(n_steps):
            lat = top_left[0] - i * lat_step
            long = top_left[1] + j * long_step
            lat_long_pairs.append((lat, long, radius))
        
    assert len(lat_long_pairs) == len(set(lat_long_pairs)), "Generated grid contains duplicate points"

    return lat_long_pairs



def get_latlong_from_bucket(project_id,
                            bucket_name,
                            latlong_list, 
                            latlong_resolution,
                            radius):

    import pandas as pd
    import numpy as np

    # use pandas to download csv from gcs bucket
    df = pd.read_csv(f"gs://{bucket_name}/{latlong_list}", header=0, dtype={'LAT': np.float64, 'LONG': np.float64})

    latlong_list = [(np.round(float(row.LAT), int(latlong_resolution)),
                     np.round(float(row.LONG), int(latlong_resolution)),
                     radius) 
                    for index, row in df.iterrows()]

    # deduplucate the latlong_list
    latlong_list = list(set(latlong_list))


    return latlong_list




def string_to_tuple(string):
    """
    Converts a string in the format "(number, number)" to a tuple of floats.

    Args:
      string: The string to convert.

    Returns:
      A tuple of floats representing the coordinates.
    """
    # Remove parentheses and split by comma
    string = string.strip('()').split(',')
    # Convert string elements to floats
    return float(string[0]), float(string[1])


def access_secret_version(project_id, secret_id, version_id="latest"):
    """
    Access the value of a secret version.

    Args:
        project_id: The Google Cloud project ID.
        secret_id: The Secret Manager secret ID.
        version_id: The Secret Manager secret version ID.

    Returns:
        The secret value.
    """

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = f"projects/{project_id}/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version.
    response = client.access_secret_version(request={"name": name})

    # Return the decoded secret value.
    return response.payload.data.decode("UTF-8")



def get_bucket_name(project_id, version_id="latest"):

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/restaurant_bucket_name/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def get_coordinates(project_id, maps_zone_name, version_id="latest"):

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    zone = maps_zone_name

    top_lef_secret_name = f'{zone}_top_left'
    bottom_right_secret_name = f'{zone}_bottom_right'

    top_left = f"projects/{project_id}/secrets/{top_lef_secret_name}/versions/{version_id}"
    bottom_right = f"projects/{project_id}/secrets/{bottom_right_secret_name}/versions/{version_id}"


    top_left_response = client.access_secret_version(request={"name": top_left})
    bottom_right_response = client.access_secret_version(request={"name": bottom_right})


    return top_left_response.payload.data.decode("UTF-8"), bottom_right_response.payload.data.decode("UTF-8")


