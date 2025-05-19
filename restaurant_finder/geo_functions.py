from geopy.distance import geodesic
from math import radians, cos, sin, atan2, pi
import googlemaps

# The function check_coordinates_are_close_to_centre was removed as it was identified as dead code.

def generate_spoke_points(center_lat, center_long, distance, num_points=6):
    """
    Generates points evenly spaced around a center point in a circle.

    Args:
        center_lat: Latitude of the center point.
        center_long: Longitude of the center point.
        radius_meters: Radius of the circle in meters.
        num_points: Number of points to generate (default: 8).

    Returns:
        List of tuples containing latitude and longitude of the generated points.
    """
    points = []
    for i in range(num_points):
        bearing = i * (360 / num_points) 

        # Calculate new point using geodesic distance and bearing
        new_point = geodesic(meters=distance).destination(
            (center_lat, center_long), bearing
        )
        points.append((new_point.latitude, new_point.longitude))
    return points
