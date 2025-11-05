# Tableau Server Statistics Scraper

Complete automation tool for scraping Tableau Server statistics and analytics data using Python, Selenium, and Polars.

## 🎯 What This Tool Does

This project provides **two powerful scrapers** for Tableau Server:

### 1. **Comprehensive Stats Scraper** (`get_tableau_stats.py`)
- **Automated end-to-end workflow** for all your Tableau workbooks
- Finds all workbooks owned by a user
- Extracts all views from each workbook
- Downloads "Who Has Seen" statistics for every view
- Fetches full names from TeamCards
- Generates summary Excel reports with pivot tables

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

1. Copy `config.example.py` to `config.ini`:
```bash
cp config.example.py config.ini
```

2. Edit `config.ini` with your settings:
```ini
[tableau]
userid = T845443
sso_username = T845443 or mathieu.drolet@telus.com
sso_password = your_password_here  # Leave blank to prompt
use_proxy = False
downloads_dir = C:/Users/T845443/Downloads
```

### Run the Stats Scraper

```bash
python get_tableau_stats.py
```

The script will:
1. ✅ Auto-detect Windows SSO (no password needed!)
2. ✅ Find all your workbooks
3. ✅ Download stats for all views
4. ✅ Fetch user full names from TeamCards
5. ✅ Generate comprehensive Excel report

## 📊 Features

### Stats Scraper (`get_tableau_stats.py`)
- 🔄 **Fully Automated** - One command to get all your Tableau stats
- 🐻‍❄️ **100% Polars** - Lightning-fast data processing
- 📝 **Excel Reports** - Professional multi-sheet output
- 👥 **TeamCards Integration** - Automatic full name lookup
- 🔐 **SSO Detection** - Works seamlessly with Windows authentication
- 💾 **Smart Caching** - Option to skip re-downloading data
- 📈 **Summary Pivots** - Automatic aggregation by workbook

## 📖 Usage Examples

### Example 1: Get All Your Tableau Stats

```python
python get_tableau_stats.py
```

Output:
- `tableau-views-by-workbook-and-view-{userid}-{date}.xlsx`
  - **Sheet 1**: Workbook Views Pivot (summary by workbook)
  - **Sheet 2**: Workbook Views Details (all view data with user info)

### Example 2: Custom Workflow with Stats Scraper

```python
from get_tableau_stats import TableauStatsScraper

with TableauStatsScraper(userid='T845443') as scraper:
    scraper.login()
    
    # Get workbooks
    workbooks = scraper.get_user_workbooks()
    
    # Download only for specific workbooks
    filtered_workbooks = workbooks.filter(
        pl.col('name').str.contains('Dashboard')
    )
    
    # Process
    scraper.get_all_views_stats(filtered_workbooks, refresh_data=True)
    views_df = scraper.parse_downloaded_files(filtered_workbooks)
    
    # Save
    views_df.write_csv('custom_report.csv')
```

## 🗂️ Project Files

### Main Scripts
- **`get_tableau_stats.py`** - Comprehensive stats scraper

### Configuration
- **`config.ini`** - Your settings (create from config.example.py)
- **`requirements.txt`** - Python dependencies

### Documentation
- **`README.md`** - This file
- **`QUICKSTART.md`** - Quick start guide

### Utilities
- **`fix_chromedriver.py`** - Clear ChromeDriver cache
- **`test_chrome_setup.py`** - Diagnostic tool

## 📋 Requirements

- Python 3.8+
- Chrome browser
- Windows (for SSO support)
- Access to Tableau Server (tableau.tsl.telus.com)
- Access to TeamCards (go/teamcards) - for full name lookup

## 🔧 Configuration Options

### config.ini Settings

```ini
[tableau]
# Your TELUS user ID
userid = T845443

# SSO username (usually same as userid)
sso_username = T845443

# SSO password (leave blank to prompt, or set for automation)
sso_password = 

# Use explicit proxy (False = use Windows system proxy)
use_proxy = False

# Where to save downloaded files
downloads_dir = C:/Users/T845443/Downloads
```

## 🎨 Output Examples

### Stats Scraper Excel Output

**Sheet 1: Workbook Views Pivot**
| Workbook name | url | workbook_id | total_views |
|--------------|-----|-------------|-------------|
| Sales Dashboard | https://... | 12345 | 1,250 |
| Marketing Analytics | https://... | 12346 | 890 |
| Finance Report | https://... | 12347 | 654 |

**Sheet 2: Workbook Views Details**
| Workbook name | View Name | workbook_id | view_id | Last Viewed | Username | views | FullName |
|--------------|-----------|-------------|---------|-------------|----------|-------|----------|
| Sales Dashboard | Overview | 12345 | 67890 | 2025-11-05 | T845443 | 25 | John Doe |
| Sales Dashboard | Regional | 12345 | 67891 | 2025-11-04 | T123456 | 18 | Jane Smith |

### Simple Scraper CSV Output

```csv
User Name,Last View Time,View Count,Department
John Doe,2025-11-05 14:30,25,Sales
Jane Smith,2025-11-04 09:15,18,Marketing
```

## 🐻‍❄️ Working with Polars

All data is returned as Polars DataFrames for maximum performance:

```python
import polars as pl

# Filter
filtered = df.filter(pl.col("views") > 10)

# Sort
sorted_df = df.sort("Last Viewed", descending=True)

# Group by and aggregate
summary = df.group_by("Username").agg([
    pl.col("views").sum().alias("total_views"),
    pl.col("View Name").n_unique().alias("unique_views")
])

# Join with other data
combined = df.join(other_df, on="Username", how="left")

# Export
df.write_csv("output.csv")
df.write_parquet("output.parquet")  # Recommended for large files
```

## 🔍 Troubleshooting

### Login Issues
- **SSO Auto-Detection**: Script automatically detects Windows SSO
- **Manual Login**: Only needed if SSO fails (rare)
- **Proxy Issues**: Set `use_proxy=False` in config.ini

### ChromeDriver Issues
```bash
# Clear ChromeDriver cache
python fix_chromedriver.py

# Test Chrome setup
python test_chrome_setup.py
```

### Missing Data
- Check Downloads folder for CSV files
- Verify view IDs are correct
- Check console output for specific errors
- Look for debug screenshots: `*_debug.png`, `*_error.png`

### TeamCards Lookup Fails
- Some users may not be in TeamCards system
- Script marks them as "UNKNOWN" and continues
- Check your network connection to go/teamcards

## 🚀 Performance Tips

1. **Use Polars** - Already implemented! 5-10x faster than pandas
2. **Skip Refresh** - Set `refresh_data=False` to reprocess existing files
3. **Headless Mode** - Run browser in background: `scraper.setup_driver(headless=True)`
4. **Parquet Format** - Use `.write_parquet()` for large datasets

## 📚 Additional Resources

- **Quick Start**: See `QUICKSTART.md`

## 🤝 Contributing

This is an internal TELUS tool. For issues or improvements, update the scripts and documentation.
You can also reach out to mathieu.drolet@telus.com for support.

## 📄 License

Internal use only - TELUS Corporation

