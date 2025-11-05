"""
Quick test script to verify Chrome driver setup
"""
import sys
import os

proxy = 'http://198.161.14.25:8080'

os.environ['http_proxy'] = proxy
os.environ['HTTP_PROXY'] = proxy
os.environ['https_proxy'] = proxy
os.environ['HTTPS_PROXY'] = proxy

def test_chrome_basic():
    """Test basic Chrome setup without webdriver-manager"""
    print("="*80)
    print("Test 1: Basic Chrome Setup (No webdriver-manager)")
    print("="*80)
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        print("Attempting to create Chrome driver...")
        driver = webdriver.Chrome(options=chrome_options)
        print("✓ Success! Chrome driver created")

        print("Testing navigation...")
        driver.get("https://www.google.com")
        print(f"✓ Page title: {driver.title}")

        driver.quit()
        print("✓ Test 1 PASSED\n")
        return True

    except Exception as e:
        print(f"✗ Test 1 FAILED: {e}\n")
        return False


def test_chrome_with_manager():
    """Test Chrome setup with webdriver-manager"""
    print("="*80)
    print("Test 2: Chrome Setup with webdriver-manager")
    print("="*80)
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager

        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')

        print("Downloading/installing ChromeDriver (this may take a moment)...")
        service = Service(ChromeDriverManager().install())

        print("Creating Chrome driver...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        print("✓ Success! Chrome driver created")

        print("Testing navigation...")
        driver.get("https://www.google.com")
        print(f"✓ Page title: {driver.title}")

        driver.quit()
        print("✓ Test 2 PASSED\n")
        return True

    except Exception as e:
        print(f"✗ Test 2 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_chrome_info():
    """Display Chrome browser information"""
    print("="*80)
    print("Chrome Browser Information")
    print("="*80)

    import subprocess
    import os

    # Check if Chrome is installed
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]

    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            print(f"✓ Chrome found at: {path}")
            chrome_found = True

            # Try to get Chrome version
            try:
                result = subprocess.run([path, "--version"], capture_output=True, text=True, timeout=5)
                if result.stdout:
                    print(f"  Version: {result.stdout.strip()}")
            except Exception as e:
                print(f"  Could not get version: {e}")
            break

    if not chrome_found:
        print("✗ Chrome browser not found in standard locations")
        print("  Please ensure Chrome is installed")

    print()


if __name__ == "__main__":
    print("\n" + "="*80)
    print("Chrome WebDriver Diagnostic Tool")
    print("="*80 + "\n")

    # Display Chrome info
    test_chrome_info()

    # Test basic setup first
    test1_passed = test_chrome_basic()

    # Always try webdriver-manager test
    print("Testing with webdriver-manager...\n")
    test_chrome_with_manager()

    print("\n" + "="*80)
    print("Diagnostic complete!")
    print("="*80)

