from data_processing import iterate_over_calls, update_json_and_save, upload_restaurants_to_bigquery
from aux_functions import get_bucket_name, string_to_tuple, get_latlong_from_bucket
from geo_functions import generate_spoke_points
import argparse
from datetime import datetime
import os
import random # Moved here as it's used in find_restaurants_in_batches


def find_restaurants_in_batches(latlong_list_input: list[tuple[float, float, int]], 
                                project_id_input: str, 
                                radius_input: int, # Although radius is part of latlong_list_input, it's kept for consistency with original args
                                limit_input: int, 
                                amount_of_noise_input: float):
    """
    Finds restaurants in batches based on a list of latitude/longitude points.

    Args:
        latlong_list_input: A list of tuples, where each tuple is (latitude, longitude, radius_for_point).
        project_id_input: The Google Cloud Project ID.
        radius_input: The default search radius (integer) - used if not in latlong_list_input tuples.
        limit_input: The limit for the number of points to process.
        amount_of_noise_input: The amount of noise to add to coordinates.

    Returns:
        A dictionary of restaurants found.
    """
    
    # Get bucket name here as it's needed for saving results
    restaurant_bucket_name = get_bucket_name(project_id=project_id_input, version_id="latest")

    # Apply limit
    n_points = len(latlong_list_input)
    if n_points > limit_input:
        print(f"Number of points {n_points} is above the set limit of {limit_input}")
        print("Going to randomly sample the points")
        random_indices = random.sample(range(n_points), limit_input)
        latlong_list_processed = [latlong_list_input[i] for i in random_indices]
    else:
        latlong_list_processed = latlong_list_input
        
    print('This is the lat long grid to be processed:', latlong_list_processed)
    print('The latlong_list_processed has', str(len(latlong_list_processed)), 'elements')

    # Pass over the grid
    restaurants, saturated_list = iterate_over_calls(latlong_list_processed, 
                                                     restaurants={}, 
                                                     project_id=project_id_input, 
                                                     amount_of_noise=amount_of_noise_input)
    print('After first grid we found', str(len(restaurants)), 'restaurants')
    print('The saturated_list has', str(len(saturated_list)), 'elements')

    # Take the saturated list and generate spoke points
    points_list: list[tuple[float, float, int]] = []
    for lat, long, radius_val in saturated_list: # Assuming radius_val from saturated_list is what we need
        points = generate_spoke_points(lat, long, 100)  # 100 meters away from point of saturation
        # Ensure radius is at least 1, e.g. by max(1, int(radius_val / 2))
        new_radius = max(1, int(radius_val / 2))
        points_with_radius = [(new_lat, new_long, new_radius) for new_lat, new_long in points]
        points_list.extend(points_with_radius)
     
    if points_list: # Only run if there are points to process
        restaurants, _ = iterate_over_calls(points_list, 
                                            restaurants=restaurants, 
                                            project_id=project_id_input, 
                                            amount_of_noise=amount_of_noise_input)
        print('After expanded list we found a TOTAL', str(len(restaurants)), 'restaurants')
    else:
        print('No points in saturated list to expand search.')

    update_json_and_save(new_data=restaurants, bucket_name=restaurant_bucket_name, project_id=project_id_input)
    
    return restaurants


if __name__ == '__main__':

    # get the project id from environment variable: 
    project_id = os.environ.get('PROJECT_ID')
    if not project_id:
        raise ValueError("PROJECT_ID environment variable not set.")
        
    parser = argparse.ArgumentParser()
    parser.add_argument("--radius", required=False, type=int, default=666)
    parser.add_argument("--latlong_list", required=False, default="postcodes/latlong.csv")
    parser.add_argument("--limit", required=False, type=int, default=20)
    parser.add_argument("--amount_of_noise", required=False, type=float, default=0.002)
    parser.add_argument("--latlong_resolution", required=False, type=int, default=2)
    args = parser.parse_args()

    print('These are the arguments passed: \n', args)

    # This part remains in main, as it prepares the input for the function
    # For command-line execution, we still fetch from bucket.
    # The Streamlit app will prepare and pass this list directly.
    restaurant_bucket_name_main = get_bucket_name(project_id=project_id, version_id="latest")
    initial_latlong_list = get_latlong_from_bucket(project_id=project_id,
                                                   bucket_name=restaurant_bucket_name_main,
                                                   latlong_list=args.latlong_list, 
                                                   latlong_resolution=args.latlong_resolution,
                                                   radius=args.radius) # args.radius is used here to construct items in initial_latlong_list

    # Call the refactored function
    found_restaurants = find_restaurants_in_batches(
        latlong_list_input=initial_latlong_list,
        project_id_input=project_id,
        radius_input=args.radius, # Pass original radius for consistency, though it's mainly used by get_latlong_from_bucket now
        limit_input=int(args.limit),
        amount_of_noise_input=float(args.amount_of_noise)
    )

    print(f"Function find_restaurants_in_batches completed. Found {len(found_restaurants)} restaurants.")

  


