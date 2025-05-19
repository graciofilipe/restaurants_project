    # "includedPrimaryTypes": ["afghani_restaurant", "african_restaurant", "american_restaurant", "asian_restaurant",
    #     "barbecue_restaurant", "brazilian_restaurant", "buffet_restaurant", "chinese_restaurant", "french_restaurant",
    #     "greek_restaurant", "hamburger_restaurant", "indian_restaurant", "indonesian_restaurant", "italian_restaurant",
    #     "japanese_restaurant", "korean_restaurant", "lebanese_restaurant", "mediterranean_restaurant", "mexican_restaurant",
    #     "middle_eastern_restaurant", "pizza_restaurant", "ramen_restaurant", "restaurant", "seafood_restaurant",
    #     "spanish_restaurant", "steak_house", "sushi_restaurant", "thai_restaurant", 
    #     "turkish_restaurant", "vegetarian_restaurant", "vietnamese_restaurant"],
    # "excludedPrimaryTypes": ["acai_shop", "bagel_shop", "bakery", "bar", "bar_and_grill", "breakfast_restaurant",
    #     "brunch_restaurant", "cafe", "cafeteria", "candy_store", "cat_cafe", "chocolate_factory", "chocolate_shop", "coffee_shop",
    #     "confectionery", "deli", "dessert_restaurant", "dessert_shop", "dog_cafe", "donut_shop", "fast_food_restaurant",
    #     "fine_dining_restaurant", "food_court", "ice_cream_shop", "juice_shop", "meal_delivery", "meal_takeaway", "pub",
    #     "sandwich_shop", "tea_house", "vegan_restaurant", "wine_bar"],
    # "excludedTypes": ["acai_shop", "bagel_shop", "bakery", "bar", "candy_store", "cat_cafe", "chocolate_factory", 
    #     "chocolate_shop", "coffee_shop", "dessert_restaurant", "dessert_shop", "dog_cafe", "donut_shop",
    #     "fast_food_restaurant", "food_court", "ice_cream_shop", "juice_shop", "pub",
    #     "sandwich_shop", "tea_house","wine_bar"],



INCLUDED_PRIMARY_TYPES = ["afghani_restaurant", "african_restaurant", "american_restaurant", "asian_restaurant",
        "barbecue_restaurant", "brazilian_restaurant", "buffet_restaurant", "chinese_restaurant", "french_restaurant",
        "greek_restaurant", "hamburger_restaurant", "indian_restaurant", "indonesian_restaurant", "italian_restaurant",
        "japanese_restaurant", "korean_restaurant", "lebanese_restaurant", "mediterranean_restaurant", "mexican_restaurant",
        "middle_eastern_restaurant", "pizza_restaurant", "ramen_restaurant", "restaurant", "seafood_restaurant",
        "spanish_restaurant", "steak_house", "sushi_restaurant", "thai_restaurant", 
        "turkish_restaurant", "vegetarian_restaurant", "vietnamese_restaurant"]

EXCLUDED_PRIMARY_TYPES = ["acai_shop", "bagel_shop", "bakery", "bar", "bar_and_grill", "breakfast_restaurant",
        "brunch_restaurant", "cafe", "cafeteria", "candy_store", "cat_cafe", "chocolate_factory", "chocolate_shop", "coffee_shop",
        "confectionery", "deli", "dessert_restaurant", "dessert_shop", "dog_cafe", "donut_shop", "fast_food_restaurant",
        "fine_dining_restaurant", "food_court", "ice_cream_shop", "juice_shop", "meal_delivery", "meal_takeaway", "pub",
        "sandwich_shop", "tea_house", "vegan_restaurant", "wine_bar"]

EXCLUDED_TYPES = ["acai_shop", "bagel_shop", "bakery", "bar", "candy_store", "cat_cafe", "chocolate_factory", 
        "chocolate_shop", "coffee_shop", "dessert_restaurant", "dessert_shop", "dog_cafe", "donut_shop",
        "fast_food_restaurant", "food_court", "ice_cream_shop", "juice_shop", "pub",
        "sandwich_shop", "tea_house","wine_bar"]

BIGQUERY_DATASET_ID = "restaurants_dataset"
BIGQUERY_TABLE_ID = "restaurants_table"

# Secret Manager Secret IDs
MAPS_API_KEY_SECRET_ID = "maps-key"
RESTAURANT_BUCKET_NAME_SECRET_ID = "restaurant_bucket_name"
COORDINATES_TOP_LEFT_SUFFIX = "_top_left"
COORDINATES_BOTTOM_RIGHT_SUFFIX = "_bottom_right"
