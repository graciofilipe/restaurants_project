import requests

from restaurant_finder.config import (
    EXCLUDED_PRIMARY_TYPES,
    EXCLUDED_TYPES,
    INCLUDED_PRIMARY_TYPES,
)


def send_request(lat, long, radius, rank, API_KEY):

    url = 'https://places.googleapis.com/v1/places:searchNearby'
    headers = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': API_KEY,
    'X-Goog-FieldMask': 'places.displayName,places.id,places.shortFormattedAddress,places.priceLevel,places.rating,places.primaryType,places.userRatingCount,places.types'
    }
    data = {
    "rankPreference": rank,
    "includedPrimaryTypes": INCLUDED_PRIMARY_TYPES,
    "excludedPrimaryTypes": EXCLUDED_PRIMARY_TYPES,
    "excludedTypes": EXCLUDED_TYPES,
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

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10) # Added timeout

        if response.status_code == 200:
            response_json = response.json()
            return response_json
        else:
            print(f"Error: API request failed with status code {response.status_code}")
            print(f"Response text: {response.text}")
            return {"error": f"API request failed with status code {response.status_code}", "details": response.text}

    except requests.exceptions.RequestException as e:
        print(f"Error: RequestException during API call: {e}")
        return {"error": f"RequestException: {e}"}
    except ValueError as e: # Catch errors during response.json() parsing if status was 200 but content is not valid JSON
        print(f"Error: Failed to parse JSON response: {e}")
        return {"error": f"JSON parsing error: {e}"}