# test_io.py
import datetime

TEST_FILE = "/tmp/simple_test_io.log"
print(f"Attempting to write to {TEST_FILE}...")
try:
    with open(TEST_FILE, "w") as f:
        f.write(f"Test IO script executed successfully at {datetime.datetime.now()}\n")
    print(f"Successfully wrote to {TEST_FILE}")
except Exception as e:
    print(f"Error writing to {TEST_FILE}: {e}")
    print(f"Exception type: {type(e)}")
