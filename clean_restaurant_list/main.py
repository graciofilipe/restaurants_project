import json
from datetime import datetime, timedelta
from google.cloud import storage
from aux_functions import get_bucket_name
import argparse
import os



def delete_old_entries(bucket_name, file_name, date_cutoff_str):
    """
    Uploads a JSON file from a Google Cloud Storage bucket, deletes entries older than a specified date,
    and uploads the updated file back to the bucket.

    Args:
        bucket_name: The name of the GCS bucket.
        file_name: The name of the JSON file in the bucket.
        date_cutoff_str: A string representing the date cutoff in the format "YYYY-MM-DD". 
                         Entries with "last_seen" dates older than this will be deleted.
    """

    # Convert the date cutoff string to a datetime object
    date_cutoff = datetime.strptime(date_cutoff_str, "%Y-%m-%d").date()

    # Download the JSON file from the bucket
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_name)
    json_string = blob.download_as_string().decode('utf-8')
    data = json.loads(json_string)

    # Delete entries older than the date cutoff
    updated_data = {}
    for restaurant_id, restaurant_data in data.items():
        last_seen_date = datetime.strptime(restaurant_data['last_seen'], "%Y-%m-%d").date()
        if last_seen_date >= date_cutoff:
            updated_data[restaurant_id] = restaurant_data

    # Upload the updated JSON file back to the bucket
    blob.upload_from_string(json.dumps(updated_data), content_type='application/json')

    print(f"File '{file_name}' updated in bucket '{bucket_name}' with entries older than {date_cutoff_str} removed.")


if __name__ == '__main__':

    # get the project id from environment variable: 
    project_id = os.environ.get('PROJECT_ID')
    restaurant_bucket_name = get_bucket_name(project_id=project_id, version_id="latest")
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--date_cutoff", required=True)
    parser.add_argument("--file_name", required=False, default='restaurants.json')
    
    args = parser.parse_args()

    delete_old_entries(restaurant_bucket_name, args.file_name, args.date_cutoff)
