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
TEST_ACCOUNTS_FILE = "test_accounts.json"
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
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # 1. Create test accounts file
    with open(TEST_ACCOUNTS_FILE, "w") as f:
        json.dump([MOCK_ACCOUNT], f)

    # 2. Start mock server in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give server time to start

    # 3. Setup environment variables for test
    os.environ["MEROSHARE_URL"] = f"http://localhost:{PORT}/login.html"
    os.environ["HEADLESS"] = "true"  # Set to true for background execution
    
    # We need to tell get_accounts to use our test file
    if os.path.exists("accounts.json"):
        shutil.move("accounts.json", "accounts.json.bak")
    shutil.copy(TEST_ACCOUNTS_FILE, "accounts.json")

    print("\n--- STARTING AUTOMATION TEST ---")
    try:
        run_automation()
    except Exception as e:
        print(f"Test failed with error: {e}")
    finally:
        print("\n--- TEST FINISHED ---")
        
        # Check if password was updated
        with open("accounts.json", "r") as f:
            updated_accounts = json.load(f)
            new_pass = updated_accounts[0]["MEROSHARE_PASS"]
            print(f"Final Password in accounts.json: {new_pass}")
            
            if new_pass != MOCK_ACCOUNT["MEROSHARE_PASS"]:
                print("✅ SUCCESS: Password was updated in accounts.json!")
            else:
                print("❌ FAILURE: Password was NOT updated.")

        # Cleanup
        if os.path.exists("accounts.json.bak"):
            if os.path.exists("accounts.json"):
                os.remove("accounts.json")
            shutil.move("accounts.json.bak", "accounts.json")
        if os.path.exists(TEST_ACCOUNTS_FILE):
             os.remove(TEST_ACCOUNTS_FILE)
        
        print("Cleanup complete. Mock server will stop when script exits.")
