from maps_call import send_request
import pandas as pd
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



def iterate_over_calls(lat_long_pairs, project_id):

    API_KEY= access_secret_version(project_id=project_id, secret_id='maps-key')

    restaurants = []

    for rank in ["DISTANCE", "POPULARITY"]:
        for lat, long, radius in lat_long_pairs:

            response_json = send_request(lat, long, radius, rank, API_KEY)
            
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
    
    return restaurants


def create_dataframe(restaurants):

    df_new = pd.DataFrame(restaurants, columns=['id','displayName', 'shortFormattedAddress', 'rating', 'priceLevel'])
    # remove rows with duplicated indexes
    df_new.set_index('id', inplace=True)
    df_new = df_new.loc[~df_new.index.duplicated(keep='first')]
    df_new = df_new.sort_index()

    return df_new

def update_df_and_save(df_new, bucket_name):
    df_old = pd.read_csv(f'gs://{bucket_name}/restaurants.csv', index_col='id')
    # merge the two dataframes to keep all restaurants in both dataframes
    df_updated = pd.concat([df_old, df_new], axis=0, join='outer')
    df_updated = df_updated.loc[~df_updated.index.duplicated(keep='last')]
    df_updated = df_updated.sort_index()
    df_updated.sort_values(by=['rating'], ascending=False, inplace=True)
    df_updated.to_csv(f'gs://{bucket_name}/restaurants.csv')

    # find out the rows that are in df_updated but not in df_old
    new_rows = df_updated[~df_updated.index.isin(df_old.index)]
    new_rows.to_csv(f'gs://{bucket_name}/new_restaurants_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    print(df_updated)
    print('NEW RESTAURANTS')
    print(new_rows)