from playwright.sync_api import sync_playwright

def inspect_nic_asia():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        print("Navigating to NIC Asia...")
        page.goto("https://omni.nicasiabank.com/sign-in", wait_until="networkidle")
        
        # We simulate the login click to see the OTP screen structure since no credentials exist locally
        page.fill("#nd-input-1", "9841000000") # dummy
        page.fill("#nd-input-0", "DummyP@ss123")
        page.click("button:has-text('Log In')")
        
        page.wait_for_timeout(5000)
        content = page.content()
        
        with open("nic_asia_debug_html.txt", "w", encoding="utf-8") as f:
            f.write(content)
            
        browser.close()

if __name__ == "__main__":
    inspect_nic_asia()
