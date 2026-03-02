import requests

token = "c700489b0c6b99e9cd72a63a236d974b09826b"
url = "https://bishal26-ipo-automation.hf.space/automation/run-all/"

headers = {
    "Authorization": f"Token {token}"
}

try:
    print(f"Triggering {url}...")
    response = requests.post(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
