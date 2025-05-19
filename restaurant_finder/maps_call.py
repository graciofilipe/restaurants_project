import requests


def send_request(lat, long, radius, rank, API_KEY):

    url = 'https://places.googleapis.com/v1/places:searchNearby'
    headers = {
    'Content-Type': 'application/json',
    'X-Goog-Api-Key': API_KEY,
    'X-Goog-FieldMask': 'places.displayName,places.id,places.shortFormattedAddress,places.priceLevel,places.rating,places.primaryType,places.userRatingCount,places.types'
    }
    data = {
    "rankPreference": rank,
    "includedPrimaryTypes": ["afghani_restaurant", "african_restaurant", "american_restaurant", "asian_restaurant",
        "barbecue_restaurant", "brazilian_restaurant", "buffet_restaurant", "chinese_restaurant", "french_restaurant",
        "greek_restaurant", "hamburger_restaurant", "indian_restaurant", "indonesian_restaurant", "italian_restaurant",
        "japanese_restaurant", "korean_restaurant", "lebanese_restaurant", "mediterranean_restaurant", "mexican_restaurant",
        "middle_eastern_restaurant", "pizza_restaurant", "ramen_restaurant", "restaurant", "seafood_restaurant",
        "spanish_restaurant", "steak_house", "sushi_restaurant", "thai_restaurant", 
        "turkish_restaurant", "vegetarian_restaurant", "vietnamese_restaurant"],
    "excludedPrimaryTypes": ["acai_shop", "bagel_shop", "bakery", "bar", "bar_and_grill", "breakfast_restaurant",
        "brunch_restaurant", "cafe", "cafeteria", "candy_store", "cat_cafe", "chocolate_factory", "chocolate_shop", "coffee_shop",
        "confectionery", "deli", "dessert_restaurant", "dessert_shop", "dog_cafe", "donut_shop", "fast_food_restaurant",
        "fine_dining_restaurant", "food_court", "ice_cream_shop", "juice_shop", "meal_delivery", "meal_takeaway", "pub",
        "sandwich_shop", "tea_house", "vegan_restaurant", "wine_bar"],
    "excludedTypes": ["acai_shop", "bagel_shop", "bakery", "bar", "candy_store", "cat_cafe", "chocolate_factory", 
        "chocolate_shop", "coffee_shop", "dessert_restaurant", "dessert_shop", "dog_cafe", "donut_shop",
        "fast_food_restaurant", "food_court", "ice_cream_shop", "juice_shop", "pub",
        "sandwich_shop", "tea_house","wine_bar"],
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