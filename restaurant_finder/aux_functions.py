from google.cloud import secretmanager
from google.cloud import storage
import numpy as np
import pandas as pd

from restaurant_finder.config import (
    COORDINATES_BOTTOM_RIGHT_SUFFIX,
    COORDINATES_TOP_LEFT_SUFFIX,
    RESTAURANT_BUCKET_NAME_SECRET_ID,
)

# Imports moved from get_latlong_from_bucket
# import pandas as pd # Already imported at the top
# import numpy as np # Already imported at the top


def get_latlong_from_bucket(project_id,
                            bucket_name,
                            latlong_list, 
                            latlong_resolution,
                            radius):

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
    name = f"projects/{project_id}/secrets/{RESTAURANT_BUCKET_NAME_SECRET_ID}/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def get_coordinates(project_id, maps_zone_name, version_id="latest"):

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    zone = maps_zone_name

    top_lef_secret_name = f'{zone}{COORDINATES_TOP_LEFT_SUFFIX}'
    bottom_right_secret_name = f'{zone}{COORDINATES_BOTTOM_RIGHT_SUFFIX}'

    top_left = f"projects/{project_id}/secrets/{top_lef_secret_name}/versions/{version_id}"
    bottom_right = f"projects/{project_id}/secrets/{bottom_right_secret_name}/versions/{version_id}"


    top_left_response = client.access_secret_version(request={"name": top_left})
    bottom_right_response = client.access_secret_version(request={"name": bottom_right})


    return top_left_response.payload.data.decode("UTF-8"), bottom_right_response.payload.data.decode("UTF-8")


