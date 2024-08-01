from maps_call import send_request
import pandas as pd
from google.cloud import secretmanager
from datetime import datetime
from google.cloud import storage


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



def iterate_over_calls(lat_long_pairs, project_id):

    API_KEY= access_secret_version(project_id=project_id, secret_id='maps-key')

    restaurants = {}
    
    today = datetime.today()
    formatted_date = today.strftime("%Y-%m-%d")

    for rank in ["DISTANCE", "POPULARITY"]:
        for lat, long, radius in lat_long_pairs:

            response_json = send_request(lat, long, radius, rank, API_KEY)
            
            try:
                for place in response_json['places']:
                    restaurants[place['id']] = {
                        'displayName': place['displayName']['text'],
                        'shortFormattedAddress': place['shortFormattedAddress'],
                        'rating': place.get('rating', 0),
                        'priceLevel': place.get('priceLevel', "NA"),
                        'last_seen': formatted_date,
                    }
            except:
                print(str(lat) + str(long) +' had no results')
                pass
    return restaurants




def read_old_restaurants(bucket_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(f'gs://{bucket_name}/restaurants.json')
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

      

    print("** new restaurants **")
    print(new_restaurants)


    # Create a new dictionary to store the concatenated results
    concatenated_dict = json_old.copy()

    # Update the concatenated dictionary with values from dict2
    concatenated_dict.update(new_restaurants)


    # write json_old and new_restaurants into cloud storage:
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    blob = bucket.blob(f'gs://{bucket_name}/restaurants_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    blob.upload_from_string(json.dumps(new_restaurants), content_type='application/json')

    blob = bucket.blob(f'gs://{bucket_name}/restaurants_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
    blob.upload_from_string(json.dumps(json_old), content_type='application/json')