from data_processing import iterate_over_calls, update_json_and_save, upload_restaurants_to_bigquery
from aux_functions import get_bucket_name, get_coordinates, build_lat_long_grid, string_to_tuple
from geo_functions import generate_spoke_points
import argparse
from datetime import datetime
import os



if __name__ == '__main__':

    # get the project id from environment variable: 
    project_id = os.environ.get('PROJECT_ID')
    restaurant_bucket_name = get_bucket_name(project_id=project_id, version_id="latest")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--n_steps", required=False, default=3)
    parser.add_argument("--radius", required=False, default=6666)
    parser.add_argument("--maps_zone_name", required=True)
    
    args = parser.parse_args()

    top_left, bottom_right = get_coordinates(project_id=project_id, version_id="latest", maps_zone_name=args.maps_zone_name)

    lat_long_grid = build_lat_long_grid(string_to_tuple(top_left),
                                        string_to_tuple(bottom_right),
                                        int(args.n_steps),
                                        int(args.radius))

    print('this is the lat long grid', lat_long_grid)

    # pass over the grid
    restaurants, saturated_list = iterate_over_calls(lat_long_grid, restaurants={}, project_id=project_id)
    print('after first grid we found ', str(len(restaurants)), ' restaurants')

    # take the saturated list and generate 
    points_list = []
    for lat, long, radius in saturated_list:
        points = generate_spoke_points(lat, long, 100) # 100 meters away from point of saturation
        points_with_radius = [(new_lat, new_long, radius/2) for new_lat, new_long in points]
        points_list = points_list + points_with_radius
    
    
    restaurants, _ = iterate_over_calls(points_list, restaurants=restaurants, project_id=project_id)

    print('after expended list we found a TOTAL', str(len(restaurants)), ' restaurants')

    update_json_and_save(new_data=restaurants, bucket_name=restaurant_bucket_name)
    upload_restaurants_to_bigquery(concatenated_dict=restaurants, project_id=project_id)

  


