from google.cloud import secretmanager
from data_processing import iterate_over_calls, create_dataframe, update_df_and_save
import argparse
from datetime import datetime




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

    parser = argparse.ArgumentParser()
    parser.add_argument("--project_id", required=True)
    parser.add_argument("--bucket_name", required=True)
    parser.add_argument("--top_left", required=True)
    parser.add_argument("--bottom_right", required=True)
    parser.add_argument("--n_steps", required=True)
    
    args = parser.parse_args()

    import ipdb; ipdb.set_trace()

    lat_long_grid = build_lat_long_grid(string_to_tuple(args.top_left),
                                        string_to_tuple(args.bottom_right),
                                        int(args.n_steps))
    restaurants = iterate_over_calls(lat_long_grid, project_id=args.project_id)
    df_new = create_dataframe(restaurants)
    update_df_and_save(df_new, args.bucket_name)
  


