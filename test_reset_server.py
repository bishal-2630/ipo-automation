import http.server
import socketserver
import threading
import os
import time
import json
import shutil
from main import run_automation

# Configuration for test
PORT = 8080
DIRECTORY = "test_env"
TEST_ACCOUNTS_FILE = "test_accounts_result.json"  # Persistent test file
MOCK_ACCOUNT = {
    "MEROSHARE_USER": "TEST_USER_123",
    "MEROSHARE_PASS": "OldPass123!",
    "DP_NAME": "NIMB ACE CAPITAL LIMITED (10600)",
    "CRN": "TEST_CRN",
    "TPIN": "1234",
    "BANK_NAME": "TEST BANK",
    "KITTA": "10",
    "EMAIL": "kbishal177@gmail.com"
}

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def start_server():
    # Use a direct way to stop the server if needed, or just let it exit with the thread
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # 1. Create persistent test accounts file
    print(f"Creating/Resetting {TEST_ACCOUNTS_FILE}...")
    with open(TEST_ACCOUNTS_FILE, "w") as f:
        json.dump([MOCK_ACCOUNT], f, indent=4)

    # 2. Start mock server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give server time to start

    # 3. Setup environment variables for test
    os.environ["MEROSHARE_URL"] = f"http://localhost:{PORT}/login.html"
    os.environ["HEADLESS"] = "true"  # Set to true for background execution
    os.environ["ACCOUNTS_FILE"] = TEST_ACCOUNTS_FILE # POINT TO OUR TEST FILE

    print("\n--- STARTING AUTOMATION TEST ---")
    print(f"Test will operate on: {TEST_ACCOUNTS_FILE}")
    print(f"Your real 'accounts.json' will NOT be touched.\n")
    
    try:
        run_automation()
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        print("\n--- TEST FINISHED ---")
        
        # Check if password was updated
        with open(TEST_ACCOUNTS_FILE, "r") as f:
            updated_accounts = json.load(f)
            new_pass = updated_accounts[0]["MEROSHARE_PASS"]
            print(f"Final Password in {TEST_ACCOUNTS_FILE}: {new_pass}")
            
            if new_pass != MOCK_ACCOUNT["MEROSHARE_PASS"]:
                print(f"✅ SUCCESS: Password was updated in {TEST_ACCOUNTS_FILE}!")
            else:
                print("❌ FAILURE: Password was NOT updated.")

        print("\n--- VERIFICATION ---")
        print(f"You can now open '{TEST_ACCOUNTS_FILE}' to see the results.")
        print("This file will remain here even after the script exits.")
        
        # Optional cleanup of technical temp files (but keep the result file)
        if os.path.exists("test_accounts.json"):
             os.remove("test_accounts.json")
        
        print("\nMock server will stop when script exits.")
