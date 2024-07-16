import requests
import pandas as pd
import os
from google.cloud import secretmanager
from datetime import datetime


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

# Set environment variable for API key
API_KEY= access_secret_version(project_id='xxxxxxx', secret_id='yyyyyyy')

def send_request(lat_long_pairs):
  '''
  lat_long_pairs is a list of tuples of the form (lat, long)
  '''
  restaurants = []

  for rank in ["DISTANCE", "POPULARITY"]:
    for lat, long, radius in lat_long_pairs:

      url = 'https://places.googleapis.com/v1/places:searchNearby'
      headers = {
        'Content-Type': 'application/json',
        'X-Goog-Api-Key': API_KEY,
        'X-Goog-FieldMask': 'places.displayName,places.id,places.shortFormattedAddress,places.priceLevel,places.rating'
      }
      data = {
        "includedTypes": ["restaurant"],
        "rankPreference": rank,
        "excludedTypes": ["bar", "cafe", "coffee_shop", "fast_food_restaurant", "ice_cream_shop", "sandwich_shop"],
        "locationRestriction": {
          "circle": {
            "center": {
              "latitude": lat,
              "longitude": long
            },
            "radius": radius
            }
        }
      }
      
      response = requests.post(url, headers=headers, json=data)
      response_json = response.json()

      try:
        for place in response_json['places']:
          restaurants.append({
            'displayName': place['displayName']['text'],
            'shortFormattedAddress': place['shortFormattedAddress'],
            'rating': place.get('rating', 0),
            'priceLevel': place.get('priceLevel', "NA"),
            'id': place['id'],

          })
      except:
        print(str(lat) + str(long) +' had no results')
        pass
    
    
  df_new = pd.DataFrame(restaurants, columns=['id','displayName', 'shortFormattedAddress', 'rating', 'priceLevel'])
  # remove rows with duplicated indexes - the same restaurant can be found in more than once call
  df_new.set_index('id', inplace=True)
  df_new = df_new.loc[~df_new.index.duplicated(keep='first')]
  df_new = df_new.sort_index()
  
  #get the old record of all restaurants  
  df_old = pd.read_csv('gs://your-bucket-name/restaurants.csv', index_col='id')
  
  # merge the two dataframes to keep all restaurants in both dataframes
  df_updated = pd.concat([df_old, df_new], axis=0, join='outer')

  # remove duplicates (restaurants found last week AND this week)
  df_updated = df_updated.loc[~df_updated.index.duplicated(keep='last')]
  df_updated = df_updated.sort_index()
  df_updated.sort_values(by=['rating'], ascending=False, inplace=True)

  # write back all (old and new) restaurants
  df_updated.to_csv('gs://your-bucket-name/restaurants.csv')

  # find out the rows that are in df_updated but not in df_old
  new_rows = df_updated[~df_updated.index.isin(df_old.index)]
  new_rows.to_csv(f'gs://your-bucket-name/new_restaurants_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
  print(df_updated)
  print('NEW RESTAURANTS')
  print(new_rows)
  

# replace these
top_left = ('lat', 'long')
bottom_right =  ('lat', 'long')
# create a 10 by 10 grid between the top left and bottom right:
n_steps = 10
lat_step = (top_left[0] - bottom_right[0]) / n_steps
long_step = (bottom_right[1] - top_left[1]) / n_steps
lat_long_pairs = []
for i in range(n_steps):
  for j in range(n_steps):
    lat = top_left[0] - i * lat_step
    long = top_left[1] + j * long_step
    lat_long_pairs.append((lat, long, 400))


if __name__ == '__main__':
  send_request(lat_long_pairs)

