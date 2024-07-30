import requests
import pandas as pd
import os
from datetime import datetime


def send_request(lat, long, radius, rank, API_KEY):

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
    return response_json