import json
from datetime import datetime
import pandas as pd
from google.cloud import storage
from google.cloud import bigquery

from restaurant_finder.aux_functions import access_secret_version
from restaurant_finder.maps_call import send_request
from restaurant_finder.config import (
    BIGQUERY_DATASET_ID,
    BIGQUERY_TABLE_ID,
    MAPS_API_KEY_SECRET_ID,
)



def iterate_over_calls(lat_long_pairs, restaurants, project_id, amount_of_noise):
    import numpy as np

    API_KEY = access_secret_version(project_id=project_id, secret_id=MAPS_API_KEY_SECRET_ID)

    saturated_list = []
    
    today = datetime.today()
    formatted_date = today.strftime("%Y-%m-%d")

    rank = "DISTANCE"  # Rank is always "DISTANCE", so set it directly
    print(f'starting the {rank} based analysis')

    for lat, long, radius in lat_long_pairs:
        lat_noise = np.random.normal(0, amount_of_noise)
        lat = lat + lat_noise
        long_noise = np.random.normal(0, amount_of_noise)
        long = long + long_noise


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



def upload_restaurants_to_bigquery(concatenated_dict, project_id):
    client = bigquery.Client(project=project_id)
    table_ref = f"{project_id}.{BIGQUERY_DATASET_ID}.{BIGQUERY_TABLE_ID}"

    # Note: This function implements a destructive update strategy.
    # The existing table (if any) is deleted and recreated on each run.
    # This is suitable if the table is intended to be a snapshot of the latest data.
    # For data retention or incremental updates, a different approach would be needed.
    try:
        dataset_ref = client.dataset(BIGQUERY_DATASET_ID) # Now client is defined before this line
        client.delete_table(table_ref)
        print(f"Table {BIGQUERY_TABLE_ID} deleted successfully.")
    except Exception as e:
        print(f"Table {BIGQUERY_TABLE_ID} does not exist. Creating a new table.")

    schema = [
        bigquery.SchemaField("restaurant_id", "STRING", mode="REQUIRED", description="Unique identifier for the restaurant"),
        bigquery.SchemaField("displayName", "STRING", mode="NULLABLE", description="Name of the restaurant"),
        bigquery.SchemaField("shortFormattedAddress", "STRING", mode="NULLABLE", description= "Address of the restaurant"),
        bigquery.SchemaField("rating", "FLOAT", mode="NULLABLE", description="Average rating of the restaurant"),
        bigquery.SchemaField("priceLevel", "STRING", mode="NULLABLE", description="Price level of the restaurant - categorical variable"),
        bigquery.SchemaField("last_seen", "DATE", mode="NULLABLE", description="Date when the restaurant was last seen active"),
        bigquery.SchemaField("first_seen", "DATE", mode="NULLABLE", description="Date when the restaurant was first seen active"),
        bigquery.SchemaField("primary_type", "STRING", mode="NULLABLE", description="Primary type of the restaurant (for example, restaurant, or italian_restaurant)"),
        bigquery.SchemaField("user_rating_count", "INTEGER", mode="NULLABLE", description="Number of users who rated the restaurant"),
        bigquery.SchemaField("types", "STRING", mode="REPEATED", description="A list of types associated with the restaurant - for example italian_restaurant or indonesian_restaurant - each restaurant can have multiple types")
    ]
    
    # The client is already created, no need to create it again.
    dataset_ref = client.dataset(BIGQUERY_DATASET_ID)
    table = bigquery.Table(table_ref, schema=schema)
    # Try to create the table. If it already exists, this might raise an error,
    # which should be fine if the deletion logic failed silently or if the table
    # truly didn't exist before. Consider adding exists_ok=True if appropriate for the API version.
    try:
        table = client.create_table(table)  # Make an API request.
        print(f"Created table {table.project}.{table.dataset_id}.{table.table_id}")
    except Exception as e: # Catch exception if table already exists
        print(f"Table {table_ref} might already exist or another error occurred: {e}")
        # If the table is needed for subsequent operations, ensure it's referenced correctly
        # This assumes that if creation fails because it exists, we can still use it.
        table = client.get_table(table_ref) # Ensure table object is valid for next step

    # table_ref is already correctly defined.
    # table_ref = dataset_ref.table(BIGQUERY_TABLE_ID) # This line is redundant

    rows_to_insert = []
    for restaurant_id, restaurant_data in concatenated_dict.items():
        row = {
            'restaurant_id': restaurant_id,
            'displayName': restaurant_data.get('displayName', 'NA'),
            'shortFormattedAddress': restaurant_data.get('shortFormattedAddress', 'NA'),
            'rating': restaurant_data.get('rating', 0),
            'priceLevel': restaurant_data.get('priceLevel', 'NA'),
            'last_seen': restaurant_data.get('last_seen', None),
            'first_seen': restaurant_data.get('first_seen', None),
            'primary_type': restaurant_data.get('primary_type', None),
            'user_rating_count': restaurant_data.get('user_rating_count', 0),
            'types': restaurant_data.get('types', [''])
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




def update_json_and_save(new_data, bucket_name, project_id):
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
    upload_restaurants_to_bigquery(concatenated_dict, project_id)




# The functions recurse_over_calls and is_point_inside_polygon were removed as they were identified as dead code.
# check_coordinates_are_close_to_centre (originally in geo_functions.py) was also part of this dead code.
