from google.cloud import secretmanager
from data_processing import iterate_over_calls, read_old_restaurants, update_json_and_save, recurse_over_calls
import argparse
from datetime import datetime
from google.cloud import secretmanager
from datetime import datetime
import os
from geopy.distance import geodesic





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


def check_coordinates_are_close_to_centre(API, lat, long, center, walking_threshold=20):
    gmaps = googlemaps.Client(key=API)
    point1 = (lat, long)
    dm = gmaps.distance_matrix(point1, center, mode='walking')
    walking_minutes = (dm['rows'][0]['elements'][0]['duration']['value'])/60
    return walking_minutes < walking_threshold


def generate_spoke_points(center_lat, center_long, radius_meters, num_points=4):
    """
    Generates points evenly spaced around a center point in a circle.

    Args:
        center_lat: Latitude of the center point.
        center_long: Longitude of the center point.
        radius_meters: Radius of the circle in meters.
        num_points: Number of points to generate (default: 8).

    Returns:
        List of tuples containing latitude and longitude of the generated points.
    """
    points = []
    for i in range(num_points):
        bearing = i * (360 / num_points) 

        # Calculate new point using geodesic distance and bearing
        new_point = geodesic(meters=radius_meters).destination(
            (center_lat, center_long), bearing
        )
        points.append((new_point.latitude, new_point.longitude, radius_meters))
    return points



if __name__ == '__main__':

    # get the project id from environment variable: 
    project_id = os.environ.get('PROJECT_ID')
    restaurant_bucket_name = get_bucket_name(project_id=project_id, version_id="latest")
    top_left, bottom_right = get_coordinates(project_id=project_id, version_id="latest")

    parser = argparse.ArgumentParser()
    parser.add_argument("--n_steps", required=False, default=5)
    
    args = parser.parse_args()

    lat_long_grid = build_lat_long_grid(string_to_tuple(top_left),
                                        string_to_tuple(bottom_right),
                                        int(args.n_steps))

    # pass over the grid
    restaurants, saturated_list = iterate_over_calls(lat_long_grid, restaurants={}, project_id=project_id)
    
    # take the saturated list and generate 
    points_list = []
    for lat, long, radius in saturated_list:
        points = generate_spoke_points(lat, long, radius)
        points_list = points_list + points
    
    import ipdb; ipdb.set_trace();
    
    restaurants, _ = iterate_over_calls(points_list, restaurants=restaurants, project_id=project_id)

    update_json_and_save(new_data=restaurants, bucket_name=restaurant_bucket_name)
  


