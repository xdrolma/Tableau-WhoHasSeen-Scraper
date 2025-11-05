"""
Fix ChromeDriver version mismatch
This script will delete the cached ChromeDriver and download the correct version
"""
import os
import shutil
import getpass

def clear_chromedriver_cache():
    """Clear the webdriver-manager cache"""
    cache_paths = [
        os.path.expanduser("~/.wdm"),
        f"C:\\Users\\{getpass.getuser()}\\.wdm",
        os.path.join(os.path.expanduser("~"), ".wdm")
    ]

    print("="*80)
    print("ChromeDriver Cache Cleaner")
    print("="*80)

    for cache_path in cache_paths:
        if os.path.exists(cache_path):
            print(f"\nFound cache at: {cache_path}")
            try:
                # List what's in the cache
                for root, dirs, files in os.walk(cache_path):
                    for file in files:
                        if 'chromedriver' in file.lower():
                            file_path = os.path.join(root, file)
                            print(f"  - {file_path}")

                # Ask for confirmation
                response = input(f"\nDelete this cache? (y/n): ").strip().lower()
                if response == 'y':
                    shutil.rmtree(cache_path)
                    print(f"✓ Deleted: {cache_path}")
                else:
                    print("  Skipped")
            except Exception as e:
                print(f"✗ Error deleting {cache_path}: {e}")
        else:
            print(f"Cache not found at: {cache_path}")

    print("\n" + "="*80)
    print("Cache cleanup complete!")
    print("="*80)
    print("\nNext steps:")
    print("1. Run your scraper script again")
    print("2. The correct ChromeDriver will be downloaded automatically")
    print("="*80)


if __name__ == "__main__":
    clear_chromedriver_cache()

