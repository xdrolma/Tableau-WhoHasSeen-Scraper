"""
Tableau Statistics Scraper
Scrapes Tableau server for Who Has Seen This data
Created on: 2025-11-05
By: Mathieu Drolet (mathieu.drolet@telus.com)
"""

import os
import re
import time
import glob
import getpass
import polars as pl
import configparser as cp

from bs4 import BeautifulSoup
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

# Switching dir to the script dir
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Load configuration
config = cp.ConfigParser()
config.read("./config.ini")

USER_ID = config.get("tableau", "userid")
SSO_USR = config.get("tableau", "sso_username")
SSO_PWD = config.get("tableau", "sso_password")
USE_PROXY = config.get("tableau", "use_proxy")

class TableauStatsScraperError(Exception):
    """Custom exception for Tableau scraper errors"""

    pass


class TableauStatsScraper:
    """
    Scraper for Tableau Server statistics
    """

    def __init__(self, userid=USER_ID, sso_username=SSO_USR, sso_password=SSO_PWD, use_proxy=USE_PROXY):
        """
        Initialize the scraper
        Args:   userid (str): User ID (e.g., 'T845443')
                sso_username (str): SSO username for authentication
                sso_password (str): SSO password for authentication
                use_proxy (bool): Whether to use explicit proxy settings
        """
        self.userid = userid
        self.sso_username = sso_username or userid
        self.sso_password = sso_password
        self.use_proxy = use_proxy
        self.proxy = "198.161.14.25:8080"
        self.base_url = "https://tableau.tsl.telus.com"
        self.downloads_dir = config.get("tableau", "downloads_dir")
        self.driver = None

    def setup_driver(self, headless=False):
        """
        Set up the Chrome WebDriver with download preferences
        Args: headless (bool): Run browser in headless mode
        """
        # Clear proxy environment variables to use Windows system proxy
        no_proxy = "localhost,127.0.0.1,::1"
        os.environ["no_proxy"] = no_proxy
        os.environ["NO_PROXY"] = no_proxy

        if not self.use_proxy:
            # Clear proxy environment variables to use Windows system settings
            for var in ["http_proxy", "HTTP_PROXY", "https_proxy", "HTTPS_PROXY"]:
                os.environ.pop(var, None)

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless=new")

        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # Set download preferences
        prefs = {
            "download.default_directory": self.downloads_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)

        # Ensure localhost is always bypassed for ChromeDriver communication
        chrome_options.add_argument(
            '--host-resolver-rules="MAP * ~NOTFOUND , EXCLUDE localhost"'
        )

        if not self.use_proxy:
            print(
                "Using system proxy settings (recommended for corporate environments)..."
            )
        else:
            print(f"Using explicit proxy: {self.proxy}")
            chrome_options.add_argument(f"--proxy-server=http://{self.proxy}")
            chrome_options.add_argument(f"--proxy-bypass-list={no_proxy}")

        print("Setting up Chrome driver...")

        # Try with webdriver-manager first, then fallback
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            print("✓ Chrome driver setup successful (automatic management)!")
        except Exception as e2:
            print(f"✗ Method 2 failed: {e2}")
            raise TableauStatsScraperError("Failed to setup Chrome driver")

        self.driver.implicitly_wait(10)

    def login(self, skip_if_logged_in=True):
        """
        Log in to Tableau Server (auto-detects SSO)
        Args: skip_if_logged_in (bool): Skip login if already authenticated via SSO
        """
        print(f"Navigating to {self.base_url}...")
        self.driver.get(self.base_url)
        time.sleep(3)

        current_url = self.driver.current_url
        page_title = self.driver.title
        print(f"Current URL: {current_url}")
        print(f"Page title: {page_title}")

        # Check if already logged in (SSO)
        if skip_if_logged_in and (
            "/#/site" in current_url or "Tableau Server" in page_title
        ):
            print("✓ Already logged in via SSO or existing session")
            return

        # If manual login needed (shouldn't happen with SSO)
        print("Manual login required...")
        if not self.sso_password:
            self.sso_password = getpass.getpass("Enter your Tableau password: ")

    def get_user_workbooks(self):
        """
        Get all workbooks belonging to the user
        Returns: pl.DataFrame: DataFrame with workbook names, URLs, and IDs
        """
        url = f"{self.base_url}/#/site/tqbi/user/corp.ads/{self.userid}/content"
        print(f"\nNavigating to user page: {url}")
        self.driver.get(url)
        self.driver.maximize_window()
        time.sleep(5)

        print("Extracting workbook links...")
        xpath = '//*[@id="app-root"]/div/div[1]/div/div/div/div[2]/div[2]/div/div[3]/div/div/div[2]/div[1]/div/div/div[2]/div/div/div/div[4]/div/span/a'

        try:
            elements = self.driver.find_elements(By.XPATH, xpath)

            workbooks_data = []
            for el in elements:
                name = el.text
                url = el.get_attribute("href")
                if url and "workbooks" in url:
                    workbook_id = re.search(r"\d+$", url)
                    workbook_id = workbook_id.group() if workbook_id else None
                    workbooks_data.append(
                        {"name": name, "url": url, "workbook_id": workbook_id}
                    )

            tableau_df = pl.DataFrame(workbooks_data)
            print(f"✓ Found {len(tableau_df)} workbooks")
            return tableau_df

        except Exception as e:
            print(f"✗ Error extracting workbooks: {e}")
            raise

    def download_view_stats(self, view_id, workbook_id):
        """
        Download 'Who Has Seen' stats for a specific view
        Args:   view_id (str): View ID
                workbook_id (str): Workbook ID (for filename)
        Returns:str: Path to downloaded file
        """
        url = f"{self.base_url}/vizql/showadminview/views/WhoHasSeen?views_id={view_id}"
        print(f"  Downloading stats for view {view_id}...")

        try:
            self.driver.get(url)
            time.sleep(3)

            # Click download button
            download_btn = self.driver.find_element(By.XPATH, '//*[@id="download"]')
            download_btn.click()

            # Navigate menu with arrow keys
            menu = self.driver.find_element(
                By.XPATH, '//*[@id="viz-viewer-toolbar-download-menu"]'
            )
            menu.send_keys(Keys.ARROW_DOWN)
            menu.send_keys(Keys.ENTER)
            time.sleep(1)

            # Handle popup window
            handles = self.driver.window_handles
            original_window = self.driver.current_window_handle

            # Switch to popup
            self.driver.switch_to.window(handles[1])
            time.sleep(1)

            # Click download button in popup
            download_popup_btn = self.driver.find_element(
                By.XPATH, "/html/body/div[1]/div/div/div/div[2]/div[1]/div[2]/button"
            )
            download_popup_btn.click()

            # Switch back to main window
            self.driver.switch_to.window(original_window)

            # Close popup dialog
            close_btn = self.driver.find_element(
                By.XPATH, "/html/body/div[6]/div/div/div/div/div[3]/div/div/button"
            )
            close_btn.click()
            time.sleep(3)

            # Rename file with workbook and view IDs
            old_file = os.path.join(self.downloads_dir, "Who Has Seen_data.csv")
            new_file = os.path.join(
                self.downloads_dir, f"Who Has Seen_data-{workbook_id}-{view_id}.csv"
            )

            # Wait for file to be downloaded
            max_wait = 10
            for i in range(max_wait):
                if os.path.exists(old_file):
                    break
                time.sleep(1)

            if os.path.exists(old_file):
                os.rename(old_file, new_file)
                print(f"  ✓ Downloaded and saved as: {os.path.basename(new_file)}")
                return new_file
            else:
                print(f"  ✗ File not downloaded")
                return None

        except Exception as e:
            print(f"  ✗ Error downloading view {view_id}: {e}")
            return None

    def get_all_views_stats(self, tableau_df, refresh_data=True):
        """
        Get stats for all views in all workbooks
        Args:   tableau_df (pl.DataFrame): DataFrame with workbook information
                refresh_data (bool): Whether to download fresh data
        Returns:list: Paths to downloaded files
        """
        if not refresh_data:
            print("Skipping data refresh")
            return []

        downloaded_files = []

        print(f"\nProcessing {len(tableau_df)} workbooks...")

        for row in tableau_df.iter_rows(named=True):
            workbook_url = row["url"]
            workbook_id = row["workbook_id"]
            workbook_name = row["name"]

            print(f"\n{'='*80}")
            print(f"Workbook: {workbook_name}")
            print(f"URL: {workbook_url}")
            print(f"{'='*80}")

            # Load workbook page
            self.driver.get(workbook_url)
            time.sleep(3)

            # Extract view links
            xpath = '//*[@id="app-root"]/div/div[1]/div/div/div/div[2]/div[2]/div/div[3]/div/div/div[2]/div[1]/div/div/div[2]/div/div/div/div[4]/div/span/a'

            try:
                view_elements = self.driver.find_elements(By.XPATH, xpath)

                views_data = []
                for el in view_elements:
                    view_name = el.text
                    view_url = el.get_attribute("href")
                    if view_url:
                        view_id = re.search(r"\d+$", view_url)
                        view_id = view_id.group() if view_id else None
                        views_data.append(
                            {"name": view_name, "url": view_url, "view_id": view_id}
                        )

                print(f"Found {len(views_data)} views in this workbook")

                # Download stats for each view
                for view in views_data:
                    if view["view_id"]:
                        file_path = self.download_view_stats(
                            view["view_id"], workbook_id
                        )
                        if file_path:
                            downloaded_files.append(file_path)

            except Exception as e:
                print(f"✗ Error processing workbook {workbook_name}: {e}")
                continue

        print(f"\n✓ Downloaded {len(downloaded_files)} files")
        return downloaded_files

    def parse_downloaded_files(self, tableau_df):
        """
        Parse all downloaded CSV files and combine them
        Args: tableau_df (pl.DataFrame): Original workbook DataFrame
        Returns: pl.DataFrame: Combined views information
        """
        pattern = os.path.join(self.downloads_dir, "Who Has Seen_data-*.csv")
        files = glob.glob(pattern)

        print(f"\nParsing {len(files)} downloaded files...")

        all_data = []

        for file_path in files:
            filename = os.path.basename(file_path)
            try:
                # Read CSV
                df = pl.read_csv(file_path)

                # Extract IDs from filename
                workbook_id_match = re.search(r"-(\d+)-", filename)
                view_id_match = re.search(r"-(\d+)\.csv", filename)

                workbook_id = workbook_id_match.group(1) if workbook_id_match else None
                view_id = view_id_match.group(1) if view_id_match else None

                # Add IDs as columns
                df = df.with_columns(
                    [
                        pl.lit(workbook_id).alias("workbook_id"),
                        pl.lit(view_id).alias("view_id"),
                    ]
                )

                all_data.append(df)

            except Exception as e:
                print(f"  ✗ Error parsing {filename}: {e}")
                continue

        if not all_data:
            print("✗ No data files found to parse")
            return pl.DataFrame()

        # Combine all data
        views_info_df = pl.concat(all_data, how="diagonal")

        # Join with workbook info
        merged = views_info_df.join(tableau_df, on="workbook_id", how="left")

        # Clean up column names
        if "Measure Names" in merged.columns:
            merged = merged.drop("Measure Names")

        if "Measure Values" in merged.columns:
            merged = merged.rename({"Measure Values": "views"})

        if "name" in merged.columns:
            merged = merged.rename({"name": "Workbook name"})

        # Select and reorder columns
        desired_cols = [
            "Workbook name",
            "View Name",
            "workbook_id",
            "view_id",
            "url",
            "Last Viewed",
            "Username",
            "views",
        ]
        existing_cols = [col for col in desired_cols if col in merged.columns]
        merged = merged.select(existing_cols)

        views_info_df = merged

        print(f"✓ Parsed data: {len(views_info_df)} rows")
        return views_info_df

    def get_full_names_from_teamcards(self, usernames):
        """
        Fetch full names for usernames from go/teamcards
        Args: usernames (list): List of usernames to look up
        Returns: pl.DataFrame: DataFrame with Username and FullName columns
        """
        print(f"\nFetching full names for {len(usernames)} users from go/teamcards...")

        full_names_data = []

        for username in usernames:
            print(f"  Looking up: {username}")
            result = {"Username": username, "FullName": "UNKNOWN"}

            try:
                self.driver.get("https://go/teamcards")
                time.sleep(5)

                # Select dropdown
                dropdown = self.driver.find_element(
                    By.XPATH,
                    "/html/body/table[1]/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/select",
                )

                # Determine if empid or ntid
                if re.match(r"^[TX]", username, re.IGNORECASE):
                    # empid - press down 5 times
                    for _ in range(5):
                        dropdown.send_keys(Keys.ARROW_DOWN)
                else:
                    # ntid - press down 6 times
                    for _ in range(6):
                        dropdown.send_keys(Keys.ARROW_DOWN)

                # Enter search value
                search_input = self.driver.find_element(
                    By.XPATH,
                    "/html/body/table[1]/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/input[1]",
                )
                search_button = self.driver.find_element(
                    By.XPATH,
                    "/html/body/table[1]/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/input[2]",
                )

                search_input.clear()
                # Remove leading T or X
                clean_username = re.sub(r"^[TX]", "", username, flags=re.IGNORECASE)
                search_input.send_keys(clean_username)
                search_button.click()

                time.sleep(2)

                # Parse result
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, "html.parser")
                tables = soup.find_all("table")

                if tables:
                    last_table = tables[-1]
                    rows = last_table.find_all("tr")
                    if len(rows) > 1:
                        cells = rows[1].find_all("td")
                        if len(cells) > 1:
                            result["FullName"] = cells[1].get_text(strip=True)
                            print(f"    ✓ Found: {result['FullName']}")

            except Exception as e:
                print(f"    ✗ Error looking up {username}: {e}")

            full_names_data.append(result)

        return pl.DataFrame(full_names_data)

    def generate_summary_by_workbook(self, views_info_df):
        """
        Generate summary pivot table by workbook
        Args: views_info_df (pl.DataFrame): Views information DataFrame
        Returns: pl.DataFrame: Summary DataFrame with total views per workbook
        """
        print("\nGenerating summary by workbook...")

        # Sum views by workbook_id using polars
        pivot = views_info_df.group_by("workbook_id").agg(
            [pl.col("views").sum().alias("total_views")]
        )

        # Merge with workbook names and URLs
        if "Workbook name" in views_info_df.columns and "url" in views_info_df.columns:
            workbook_info = views_info_df.select(
                ["workbook_id", "Workbook name", "url"]
            ).unique()
            pivot = pivot.join(workbook_info, on="workbook_id", how="left")

        # Sort by total views
        pivot = pivot.sort("total_views", descending=True)

        # Reorder columns
        cols = ["Workbook name", "url", "workbook_id", "total_views"]
        existing_cols = [col for col in cols if col in pivot.columns]
        pivot = pivot.select(existing_cols)

        print(f"✓ Summary created: {len(pivot)} workbooks")
        return pivot

    def save_to_excel(self, pivot_df, views_info_df):
        """
        Save results to Excel file
        Args:   pivot_df (pl.DataFrame): Summary pivot DataFrame
                views_info_df (pl.DataFrame): Detailed views DataFrame
        """
        import pandas as pd  # Only import for Excel writing

        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"tableau-views-by-workbook-and-view-{self.userid}-{timestamp}.xlsx"
        filepath = os.path.join(self.downloads_dir, filename)

        print(f"\nSaving results to: {filename}")

        try:
            with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
                # Convert polars to pandas only for writing
                pivot_df.to_pandas().to_excel(
                    writer, sheet_name="Workbook Views Pivot", index=False
                )
                views_info_df.to_pandas().to_excel(
                    writer, sheet_name="Workbook Views Details", index=False
                )

            print(f"✓ Results saved to: {filepath}")
            return filepath

        except Exception as e:
            print(f"✗ Error saving Excel file: {e}")
            raise

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("\n✓ Browser closed")

    def __enter__(self):
        """Context manager entry"""
        self.setup_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


def main():
    """Main execution function"""

    # SCRIPT SETTINGS
    refresh_data = True
    userid = USER_ID if USER_ID else None
    sso_username = SSO_USR if SSO_USR else userid if userid else None
    sso_password = SSO_PWD if SSO_PWD else None

    print("=" * 80)
    print("TABLEAU STATISTICS SCRAPER")
    print("=" * 80)
    print(f"User ID: {userid}")
    print(f"Refresh data: {refresh_data}")
    print("=" * 80)

    # Use context manager for automatic cleanup
    with TableauStatsScraper(
        userid=userid,
        sso_username=sso_username,
        sso_password=sso_password,
        use_proxy=False,  # Use Windows system proxy
    ) as scraper:

        # 1. Login
        scraper.login()

        # 2. Get user workbooks
        tableau_df = scraper.get_user_workbooks()

        # 3. Download stats for all views
        scraper.get_all_views_stats(tableau_df, refresh_data=refresh_data)

        # 4. Parse downloaded files
        views_info_df = scraper.parse_downloaded_files(tableau_df)

        if len(views_info_df) == 0:
            print("\n✗ No data found. Exiting.")
            return

        # 5. Get full names from teamcards
        if "Username" in views_info_df.columns:
            usernames = views_info_df["Username"].unique().to_list()
            full_names_df = scraper.get_full_names_from_teamcards(usernames)

            # Merge with views data using polars
            views_info_df = views_info_df.join(full_names_df, on="Username", how="left")

        # 6. Generate summary by workbook
        pivot_df = scraper.generate_summary_by_workbook(views_info_df)

        # 7. Save to Excel
        scraper.save_to_excel(pivot_df, views_info_df)

        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Workbooks processed: {len(tableau_df)}")
        print(f"Total records: {len(views_info_df)}")
        print("=" * 80)
        print("\n✓ Script completed successfully!")


if __name__ == "__main__":
    main()
