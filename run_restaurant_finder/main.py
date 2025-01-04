from data_processing import iterate_over_calls, update_json_and_save, upload_restaurants_to_bigquery
from aux_functions import get_bucket_name, string_to_tuple, get_latlong_from_bucket
from geo_functions import generate_spoke_points
import argparse
from datetime import datetime
import os


if __name__ == '__main__':

    # get the project id from environment variable: 
    project_id = os.environ.get('PROJECT_ID')
    restaurant_bucket_name = get_bucket_name(project_id=project_id, version_id="latest")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--radius", required=False, default=666)
    parser.add_argument("--latlong_list", required=False, default="postcodes/latlong.csv")
    parser.add_argument("--limit", required=False, default=20)
    parser.add_argument("--amount_of_noise", required=False, default=0.002)
    parser.add_argument("--latlong_resolution", required=False, default=3)
    args = parser.parse_args()

    print('these are the arguments passed: \n', args)

    latlong_list = get_latlong_from_bucket(project_id=project_id,
                                           bucket_name=restaurant_bucket_name,
                                           latlong_list=args.latlong_list, 
                                           latlong_resolution=args.latlong_resolution,
                                           radius=args.radius)

    n_points = len(latlong_list)
     
    if n_points > int(args.limit):
        print(f"number of points {n_points} is above the set limit of {args.limit}")
        print("going to randomly sample the points")

        # extract a random args.limit number of points from latlong_list
        import random
        random_indices = random.sample(range(n_points), int(args.limit))
        sampled_latlong_list = [latlong_list[i] for i in random_indices]
        latlong_list = sampled_latlong_list
        

    print('this is the lat long grid', latlong_list)
    print('the latlong_list has ', str(len(latlong_list)), ' elements')

    # pass over the grid
    restaurants, saturated_list = iterate_over_calls(latlong_list, restaurants={}, project_id=project_id, amount_of_noise=float(args.amount_of_noise))
    print('after first grid we found ', str(len(restaurants)), ' restaurants')
    print('the saturated_list has ', str(len(saturated_list)), ' elements')

    # take the saturated list and generate 
    points_list: list[tuple[float, float, int]] = []
    for lat, long, radius in saturated_list:
        points = generate_spoke_points(lat, long, 100) # 100 meters away from point of saturation
        points_with_radius = [(new_lat, new_long, radius/2) for new_lat, new_long in points]
        points_list = points_list + points_with_radius
     
    restaurants, _ = iterate_over_calls(points_list, restaurants=restaurants, project_id=project_id)

    print('after expended list we found a TOTAL', str(len(restaurants)), ' restaurants')

    update_json_and_save(new_data=restaurants, bucket_name=restaurant_bucket_name, project_id=project_id)

  


