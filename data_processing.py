from maps_call import send_request
import pandas as pd
from google.cloud import secretmanager
from datetime import datetime
from google.cloud import storage
import json
import googlemaps
from geopy.distance import geodesic
from math import radians, cos, sin, atan2, pi



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






def iterate_over_calls(lat_long_pairs, restaurants, project_id):

    API_KEY= access_secret_version(project_id=project_id, secret_id='maps-key')

    saturated_list = []
    
    today = datetime.today()
    formatted_date = today.strftime("%Y-%m-%d")

    for rank in ["DISTANCE", "POPULARITY"]:
        for lat, long, radius in lat_long_pairs:

            response_json = send_request(lat, long, radius, rank, API_KEY)
            if 'places' not in response_json:
                print(str(lat) + str(long) +' had no results')
            
            else:
                if len(response_json['places']) == 20:
                    print(str(lat) + str(long) +' had 20 results')

                    saturated_list.append((lat, long, radius/2))
                else:
                    print(str(lat) + str(long) +' had 1-19 results')
                    for place in response_json['places']:
                        restaurants[place['id']] = {
                            'displayName': place['displayName']['text'],
                            'shortFormattedAddress': place['shortFormattedAddress'],
                            'rating': place.get('rating', 0),
                            'priceLevel': place.get('priceLevel', "NA"),
                            'last_seen': formatted_date,
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