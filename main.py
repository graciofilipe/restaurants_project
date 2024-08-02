from data_processing import iterate_over_calls, read_old_restaurants, update_json_and_save, recurse_over_calls
import argparse
from datetime import datetime
import os




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
    
    
    restaurants, _ = iterate_over_calls(points_list, restaurants=restaurants, project_id=project_id)

    update_json_and_save(new_data=restaurants, bucket_name=restaurant_bucket_name)
  


