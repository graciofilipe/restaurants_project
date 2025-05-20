# test_rf_imports.py
import sys
import traceback # Ensure traceback is imported at the top

print("--- Attempting to import from restaurant_finder.main ---")
try:
    from restaurant_finder.main import find_restaurants_in_batches
    print("Successfully imported find_restaurants_in_batches from restaurant_finder.main")
except ImportError as e:
    print(f"IMPORT_ERROR importing from restaurant_finder.main: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
except Exception as e:
    print(f"OTHER_ERROR importing from restaurant_finder.main: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

print("\n--- Attempting to import from restaurant_finder.aux_functions ---")
try:
    from restaurant_finder.aux_functions import get_latlong_from_bucket
    print("Successfully imported get_latlong_from_bucket from restaurant_finder.aux_functions")
except ImportError as e:
    print(f"IMPORT_ERROR importing from restaurant_finder.aux_functions: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
except Exception as e:
    print(f"OTHER_ERROR importing from restaurant_finder.aux_functions: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)

print("\n--- Test script finished ---")
