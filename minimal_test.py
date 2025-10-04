# minimal_test.py
print("--- Script Started ---")

try:
    from dotenv import load_dotenv
    print("SUCCESS: 'dotenv' library was imported.")
    
    found_dotenv = load_dotenv()
    print(f"SUCCESS: load_dotenv() ran. Found .env file: {found_dotenv}")

except Exception as e:
    print(f"FAILURE: An error occurred during import or load_dotenv(): {e}")

print("--- Script Finished ---")