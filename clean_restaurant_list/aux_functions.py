from google.cloud import secretmanager
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



def get_bucket_name(project_id, version_id="latest"):

    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/restaurant_bucket_name/versions/{version_id}"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
