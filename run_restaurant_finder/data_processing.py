import json
from datetime import datetime
import pandas as pd
from google.cloud import storage
from maps_call import send_request
from aux_functions import access_secret_version
from google.cloud import bigquery




def iterate_over_calls(lat_long_pairs, restaurants, project_id):

    API_KEY= access_secret_version(project_id=project_id, secret_id='maps-key')

    saturated_list = []
    
    today = datetime.today()
    formatted_date = today.strftime("%Y-%m-%d")

    for rank in ["DISTANCE"]:
        print(f'starting the {rank} based analysis')

        for lat, long, radius in lat_long_pairs:

            response_json = send_request(lat, long, radius, rank, API_KEY)
            if 'places' not in response_json:
                print(str(lat) + str(long) +' had no results')
            
            else:
                if len(response_json['places']) == 20:
                    print(str(lat) + str(long) +' had 20 results')

                    saturated_list.append((lat, long, radius))
                else:
                    print(str(lat) + str(long) +' had 1-19 results')
                    for place in response_json['places']:
                        restaurants[place['id']] = {
                            'displayName': place['displayName']['text'],
                            'shortFormattedAddress': place.get('shortFormattedAddress', 'NA'),
                            'rating': place.get('rating', 0),
                            'priceLevel': place.get('priceLevel', 'NA'),
                            'last_seen': formatted_date,
                            'primary_type': place.get('primaryType', 'NA'),
                            'user_rating_count': place.get('userRatingCount', 0),
                            'types': place.get('types', [])
                        }

    return restaurants, saturated_list




def read_old_restaurants(bucket_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob('restaurants.json')
    json_string = blob.download_as_string().decode('utf-8')
    data = json.loads(json_string)
    return data


def update_json_and_save(new_data, bucket_name):
    json_old = read_old_restaurants(bucket_name)
    
    new_restaurants = {}
    for restaurant_id, restaurant_data in new_data.items():
        
        #case one, the restaurant is new
        if restaurant_id not in json_old:
            new_restaurants[restaurant_id] = restaurant_data
            new_restaurants[restaurant_id]['first_seen'] = new_restaurants[restaurant_id]['last_seen']

        #case two, the restaurant has been seen before
        else:
            # update the rating
            json_old[restaurant_id]['rating'] = restaurant_data['rating']
            # update the address
            json_old[restaurant_id]['shortFormattedAddress'] = restaurant_data['shortFormattedAddress']
            # update the price level
            json_old[restaurant_id]['priceLevel'] = restaurant_data['priceLevel']
            # update the last_seen
            json_old[restaurant_id]['last_seen'] = restaurant_data['last_seen']
            # update the primary_type
            json_old[restaurant_id]['primary_type'] = restaurant_data['primary_type']
            # update the user_rating_count
            json_old[restaurant_id]['user_rating_count'] = restaurant_data['user_rating_count']
            # update the types
            json_old[restaurant_id]['types'] = restaurant_data['types']

      

    print("** new restaurants **")
    print(new_restaurants)


    # Create a new dictionary to store the concatenated results
    concatenated_dict = json_old.copy()

    # Update the concatenated dictionary with values from dict2
    concatenated_dict.update(new_restaurants)


    # write json_old and new_restaurants into cloud storage:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(f'restaurants_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    blob.upload_from_string(json.dumps(new_restaurants), content_type='application/json')

    blob = bucket.blob(f'restaurants.json')
    blob.upload_from_string(json.dumps(concatenated_dict), content_type='application/json')


def upload_restaurants_to_bigquery(concatenated_dict, project_id):
    client = bigquery.Client(project=project_id)
    dataset_id = 'restaurant_dataset'
    table_id = 'restaurants_table'
    dataset_ref = client.dataset(dataset_id)
    table_ref = f"{project_id}.{dataset_id}.{table_id}"
    try:
        client.get_table(table_ref)
        client.delete_table(table_ref)
        print(f"Table {table_id} deleted successfully.")
    except Exception as e:
        print(f"Table {table_id} does not exist. Creating a new table.")

    schema = [
        bigquery.SchemaField("restaurant_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("displayName", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("shortFormattedAddress", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("rating", "FLOAT", mode="NULLABLE"),
        bigquery.SchemaField("priceLevel", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("last_seen", "DATE", mode="NULLABLE"),
        bigquery.SchemaField("first_seen", "DATE", mode="NULLABLE"),
        bigquery.SchemaField("primary_type", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("user_rating_count", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("types", "STRING", mode="REPEATED")
    ]

    table = bigquery.Table(table_ref, schema=schema)
    table = client.create_table(table)  # Make an API request.
    print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")

    table_ref = dataset_ref.table(table_id)

    rows_to_insert = []
    for restaurant_id, restaurant_data in concatenated_dict.items():
        row = {
            'restaurant_id': restaurant_id,
            'displayName': restaurant_data.get('displayName', None),
            'shortFormattedAddress': restaurant_data.get('shortFormattedAddress', None),
            'rating': restaurant_data.get('rating', None),
            'priceLevel': restaurant_data.get('priceLevel', None),
            'last_seen': restaurant_data.get('last_seen', None),
            'first_seen': restaurant_data.get('first_seen', None),
            'primary_type': restaurant_data.get('primary_type', None),
            'user_rating_count': restaurant_data.get('user_rating_count', None),
            'types': restaurant_data.get('types', None)
        }
        rows_to_insert.append(row)

    try:
        errors = client.insert_rows_json(table_ref, rows_to_insert)
        if errors == []:
            print("New rows have been added.")
        else:
            print(f"Encountered errors while inserting rows: {errors}")
    except Exception as e:
        print(f"An error occurred: {e}")




















def recurse_over_calls(lat, long, center, project_id, restaurants={}, list_of_called_points=[]):
    import ipdb; ipdb.set_trace()
    rank = "DISTANCE"
    radius = 5000
    API_KEY= access_secret_version(project_id=project_id, secret_id='maps-key')
    today = datetime.today()
    formatted_date = today.strftime("%Y-%m-%d")

    if check_coordinates_are_close_to_centre(API_KEY, lat, long, center, walking_threshold=20):

        print("SENDING A REQUEST!!!!!")
        response_json = send_request(lat, long, radius, rank, API_KEY)
        list_of_called_points.append((lat, long))

        if len(response_json['places']) >= 20:
            print("** 20 results **")

            # capture the results anyway
            for place in response_json['places']:
                        restaurants[place['id']] = {
                            'displayName': place['displayName']['text'],
                            'shortFormattedAddress': place['shortFormattedAddress'],
                            'rating': place.get('rating', 0),
                            'priceLevel': place.get('priceLevel', "NA"),
                            'last_seen': formatted_date,
                        }
            # create the 9 sub distances
            new_points_list = generate_spoke_points(lat, long, radius_meters=400, num_points=4)
            accepted_points_list = [point for point in new_points_list if not is_point_inside_polygon(list_of_called_points, point[0], point[1])]
            print('accepted points list', accepted_points_list)
            # call the function over the 9 subdistances
            for point in new_points_list:
                recurse_over_calls(point[0], point[1], center, project_id, restaurants, list_of_called_points)
         
        # the base case
        elif len(response_json['places']) < 20 and len(response_json['places']) > 0:
            print("** less than 20 results **")
            # capture the results anyway
            for place in response_json['places']:
                        restaurants[place['id']] = {
                            'displayName': place['displayName']['text'],
                            'shortFormattedAddress': place['shortFormattedAddress'],
                            'rating': place.get('rating', 0),
                            'priceLevel': place.get('priceLevel', "NA"),
                            'last_seen': formatted_date,
                        }
    return restaurants

def is_point_inside_polygon(polygon_points, x1, y1):
    """
    Determines if a point is inside a polygon using the ray casting algorithm.

    Args:
        polygon_points: List of tuples representing (x, y) coordinates of the polygon's vertices.
        x1: X coordinate of the point to check.
        y1: Y coordinate of the point to check.

    Returns:
        True if the point is inside the polygon, False otherwise.
    """
    num_vertices = len(polygon_points)
    inside = False
    
    # Iterate through all edges of the polygon
    for i in range(num_vertices):
        j = (i + 1) % num_vertices  # Next vertex (wrap around to 0 if at last vertex)
        x_i, y_i = polygon_points[i]
        x_j, y_j = polygon_points[j]

        # Check if the horizontal ray from the point intersects the edge
        intersect = (y_i > y1) != (y_j > y1) and (
            x1 < (x_j - x_i) * (y1 - y_i) / (y_j - y_i) + x_i
        )
        if intersect:
            inside = not inside  # Toggle inside/outside status with each intersection
            
    return inside
