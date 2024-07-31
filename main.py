from google.cloud import secretmanager
from data_processing import iterate_over_calls, create_dataframe, update_df_and_save
import argparse
from datetime import datetime
from google.cloud import secretmanager
from datetime import datetime
import os




def get_bucket_name(project_id, version_id="latest"):

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/restaurant_bucket_name/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def get_coordinates(project_id, version_id="latest"):

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()
    
    bottom_right = f"projects/{project_id}/secrets/restaurant_top_left/versions/{version_id}"
    top_left_response = client.access_secret_version(request={"name": bottom_right})

    bottom_right = f"projects/{project_id}/secrets/restaurant_bottom_right/versions/{version_id}"
    bottom_right_response = client.access_secret_version(request={"name": bottom_right})


    return top_left_response.payload.data.decode("UTF-8"), bottom_right_response.payload.data.decode("UTF-8")



def build_lat_long_grid(top_left, bottom_right, n_steps):

    lat_step = (top_left[0] - bottom_right[0]) / n_steps
    long_step = (bottom_right[1] - top_left[1]) / n_steps
    lat_long_pairs = []
    for i in range(n_steps):
        for j in range(n_steps):
            lat = top_left[0] - i * lat_step
            long = top_left[1] + j * long_step
            lat_long_pairs.append((lat, long, 400))
    
    return lat_long_pairs


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


if __name__ == '__main__':

    # get the project id from environment variable: 
    project_id = os.environ.get('PROJECT_ID')
    print("********* PROJECT ID IS: " + project_id + " *********")

    restaurant_bucket_name = get_bucket_name(project_id=project_id, version_id="latest")
    top_left, bottom_right = get_coordinates(project_id=project_id, version_id="latest")

    parser = argparse.ArgumentParser()
    parser.add_argument("--n_steps", required=True)
    
    args = parser.parse_args()

    lat_long_grid = build_lat_long_grid(string_to_tuple(top_left),
                                        string_to_tuple(bottom_right),
                                        int(args.n_steps))

    restaurants = iterate_over_calls(lat_long_grid, project_id=project_id)

    df_new = create_dataframe(restaurants)
    update_df_and_save(df_new, restaurant_bucket_name)
  


