scrappy code to indetify local restaurants and compare them against a previous list. The goal is to find new restaurants that weren't there before. 


## Arguments for Restaurant Finder Script

This script takes the following arguments:

*   **`--radius`**:  This argument defines the radius (in meters) around each point in the latitude/longitude grid within which to search for restaurants.  The default value is 666 meters.  Increasing the radius expands the search area, potentially finding more restaurants but also increasing the likelihood of hitting the API limit.  Decreasing the radius narrows the search area.

*   **`--latlong_list`**: This argument specifies the path to the CSV file in Cloud Storage containing the latitude/longitude pairs that define the search grid. This file should contain columns named `LAT` and `LONG` representing the coordinates.  The default value is "postcodes/latlong.csv".

*   **`--limit`**:  This argument sets a limit on the number of latitude/longitude pairs to process from the input CSV.  This is useful for testing or when dealing with large datasets. If the number of points in the  `latlong_list` exceeds this limit, a random sample of points will be selected for processing.  The default value is 20.

*   **`--amount_of_noise`**:  This argument introduces random noise to the latitude and longitude coordinates. The noise is drawn from a normal distribution with a mean of 0 and a standard deviation equal to this argument's value.  This helps prevent redundant API calls when points in the grid are very close together and can distribute the search more evenly.  The default value is 0.002.

*   **`--latlong_resolution`**: This argument controls the precision of the latitude and longitude coordinates by rounding them to the specified number of decimal places. For example, a value of 3 would round coordinates to three decimal places (e.g., 34.123, -118.456).  This helps to reduce the number of unique locations and consolidate nearby searches. The default value is 3.


 - example prompt: Select the name, rating, user_rating_count, and types for the restaurants that have first_seen less than 60 days from today and have user_rating_count between 5 and 60. Order by average rating descending

SELECT
  displayName,
  rating as average_rating,
  user_rating_count as number_of_reviews, 
  shortFormattedAddress, 
  primary_type,
  types as extra_types
FROM
  `project-name.restaurants_dataset.restaurants_table`
WHERE
  DATE_DIFF(CURRENT_DATE(), first_seen, DAY) < 30
  AND user_rating_count BETWEEN 5 AND 66
  AND rating > 4
ORDER BY
  rating DESC;
