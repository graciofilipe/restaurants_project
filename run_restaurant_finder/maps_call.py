import requests


def send_request(lat, long, radius, rank, API_KEY):

    url = 'https://places.googleapis.com/v1/places:searchNearby'
    headers = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': API_KEY,
    'X-Goog-FieldMask': 'places.displayName,places.id,places.shortFormattedAddress,places.priceLevel,places.rating'
    }
    data = {
    "rankPreference": rank,
    "includedPrimaryTypes": ["american_restaurant", "barbecue_restaurant", "brazilian_restaurant",
        "chinese_restaurant",  "french_restaurant", "greek_restaurant", "hamburger_restaurant",
        "indian_restaurant" , "indonesian_restaurant", "italian_restaurant", "japanese_restaurant",
        "korean_restaurant", "lebanese_restaurant", "mediterranean_restaurant", "mexican_restaurant",
        "middle_eastern_restaurant", "pizza_restaurant",  "ramen_restaurant", "restaurant", 
        "seafood_restaurant", "spanish_restaurant", "steak_house", "sushi_restaurant", "thai_restaurant",
        "turkish_restaurant", "vegetarian_restaurant", "vietnamese_restaurant"
        ],
    "excludedPrimaryTypes": ["meal_delivery", "meal_takeaway", "fast_food_restaurant",
        "bar", "bakery", "cafe", "coffee_shop", "breakfast_restaurant",
        "ice_cream_shop", "sandwich_shop", "brunch_restaurant", "vegan_restaurant"
        ],
    "excludedTypes": ["bakery", "bar", "cafe", "coffee_shop", "breakfast_restaurant", 
        "ice_cream_shop", "sandwich_shop", "brunch_restaurant", "vegan_restaurant"],
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