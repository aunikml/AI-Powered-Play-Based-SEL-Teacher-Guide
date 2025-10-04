# api_test.py (with trace debugging)

print("--- [Checkpoint 1] Script started. Importing libraries...")

import requests
import os
import json
from dotenv import load_dotenv

print("--- [Checkpoint 2] Libraries imported. Configuring script...")

# --- SCRIPT CONFIGURATION ---
load_dotenv()
print("--- [Checkpoint 3] load_dotenv() executed.")

BASE_URL = "http://127.0.0.1:5001"
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "supersecret")
print("--- [Checkpoint 4] Environment variables loaded.")
print(f"---          Admin Email: {ADMIN_EMAIL}")


# --- HELPER FUNCTIONS ---
def print_header(title):
    """Prints a formatted header to the console."""
    print("\n" + "="*60)
    print(f"===== {title.upper()} =====")
    print("="*60)

def test_endpoint(session, method, endpoint, payload=None, description=""):
    """A generic function to test an endpoint and print the results."""
    print(f"\n[TESTING] {description} ({method} {endpoint})")
    try:
        if method.upper() == 'POST':
            response = session.post(f"{BASE_URL}{endpoint}", json=payload, timeout=90)
        else: # GET
            response = session.get(f"{BASE_URL}{endpoint}", timeout=10)

        print(f"  -> Status Code: {response.status_code}")
        try:
            print("  -> Response JSON:")
            print(json.dumps(response.json(), indent=2))
        except json.JSONDecodeError:
            print("  -> Response Body (Not JSON):")
            print(response.text)
        
        return response

    except requests.exceptions.RequestException as e:
        print(f"\n!!!!!! REQUEST FAILED !!!!!!")
        print(f"Could not connect to the backend at {BASE_URL}.")
        print("Please ensure your Flask server is running.")
        print(f"Error: {e}")
        return None

print("--- [Checkpoint 5] Helper functions defined.")

# --- MAIN TEST EXECUTION ---
if __name__ == "__main__":
    print("--- [Checkpoint 6] Main execution block started.")
    
    authenticated_session = requests.Session()
    print("--- [Checkpoint 7] Requests session created.")

    # --- 1. TEST LOGIN ---
    print_header("1. Authentication Test")
    login_payload = {"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    login_response = test_endpoint(authenticated_session, 'POST', '/api/login', login_payload, "Admin Login")
    print("--- [Checkpoint 8] Login test completed.")

    if not login_response or login_response.status_code != 200:
        print("\n!!!!!! LOGIN FAILED !!!!!!")
    else:
        print("--- [Checkpoint 9] Login successful, proceeding to authenticated tests.")
        # ... (the rest of the tests)
        print_header("2. Authenticated Teacher Endpoint Tests")
        test_endpoint(authenticated_session, 'GET', '/api/chatbot/options', description="Fetch Chatbot Options")

        print_header("3. Generate Plan Test (The Critical One)")
        plan_payload = {
            "age_cohort": "1-2 years", "subject": "Language & Literacy",
            "sub_domain": "Vocabulary building",
            "play_type": {"name": "Guided Play", "context": "Standard"}
        }
        test_endpoint(authenticated_session, 'POST', '/api/generate-plan', plan_payload, "Generate a Standard Plan")
        print("--- [Checkpoint 10] Authenticated tests completed.")

    print_header("FINAL. Unauthenticated Access Test")
    unauthenticated_session = requests.Session()
    test_endpoint(unauthenticated_session, 'GET', '/api/chatbot/options', description="Fetch Chatbot Options (Should Fail)")
    print("--- [Checkpoint 11] Script finished.")