# Quick Start Guide

## Installation

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Create configuration file:**

Copy `config.example.py` to `config.ini` and edit with your details:

```ini
[tableau]
userid = T845443
sso_username = T845443
sso_password = 
use_proxy = False
downloads_dir = C:/Users/T845443/Downloads
```

### Comprehensive Stats Scraper

**Get stats for ALL your workbooks and views in one command:**

```bash
python get_tableau_stats.py
```

This will:
- ✅ Find all your workbooks
- ✅ Download "Who Has Seen" stats for every view
- ✅ Fetch full names from TeamCards
- ✅ Generate Excel report with 2 sheets (pivot + details)

**Output:** `tableau-views-by-workbook-and-view-{userid}-{date}.xlsx`

## Finding Your View ID

1. Go to your Tableau view
2. Click on "Who Has Seen This View" admin link
3. Look at the URL:
   ```
   https://tableau.tsl.telus.com/vizql/showadminview/views/WhoHasSeen?views_id=250361
   ```
   The number after `views_id=` is your View ID (`250361`)

## Common Tasks

### Task 1: Get All Stats (First Time)

```bash
# Edit config.ini with your userid
# Run the scraper
python get_tableau_stats.py
```

Result: Excel file in your Downloads folder with complete stats

### Task 2: Refresh Only Some Workbooks

```python
from get_tableau_stats import TableauStatsScraper
import polars as pl

with TableauStatsScraper(userid='T845443') as scraper:
    scraper.login()
    workbooks = scraper.get_user_workbooks()
    
    # Filter to specific workbooks
    filtered = workbooks.filter(pl.col('name').str.contains('Dashboard'))
    
    scraper.get_all_views_stats(filtered, refresh_data=True)
    views_df = scraper.parse_downloaded_files(filtered)
    pivot_df = scraper.generate_summary_by_workbook(views_df)
    scraper.save_to_excel(pivot_df, views_df)
```

### Task 3: Re-process Existing Files (No Download)

```python
from get_tableau_stats import TableauStatsScraper

with TableauStatsScraper(userid='T845443') as scraper:
    scraper.login()
    workbooks = scraper.get_user_workbooks()
    
    # Skip downloading - just parse existing CSVs
    scraper.get_all_views_stats(workbooks, refresh_data=False)
    
    views_df = scraper.parse_downloaded_files(workbooks)
    pivot_df = scraper.generate_summary_by_workbook(views_df)
    scraper.save_to_excel(pivot_df, views_df)
```

## Working with Results

### Polars DataFrame Operations

```python
import polars as pl

# Read the data
df = pl.read_csv("who_has_seen_250361.csv")

# Filter
high_usage = df.filter(pl.col("views") > 10)

# Sort
sorted_df = df.sort("Last Viewed", descending=True)

# Group and aggregate
summary = df.group_by("Username").agg([
    pl.col("views").sum().alias("total_views")
])

# Join with other data
combined = df.join(other_df, on="Username", how="left")
```

### Export Options

```python
# CSV (universal compatibility)
df.write_csv("output.csv")

# Parquet (best for large datasets)
df.write_parquet("output.parquet")

# Convert to pandas for Excel
df.to_pandas().to_excel("output.xlsx", index=False)
```

## Troubleshooting

### "Chrome driver setup failed"
```bash
# Clear ChromeDriver cache and try again
python fix_chromedriver.py
```

### "Already logged in via SSO"
✅ This is good! The script detected your Windows authentication automatically.

### "No data found"
- Check that view ID is correct
- Verify you have access to the view
- Check Downloads folder for CSV files

### "TeamCards lookup failed"
- Some users may not be in TeamCards
- Script will mark them as "UNKNOWN" and continue
- Not critical for stats analysis

## Configuration Tips

### For Manual Password Entry
```ini
[tableau]
sso_password = 
```
Leave blank - script will prompt securely

### For Automated Runs
```ini
[tableau]
sso_password = YourPassword123
```
Set password - no prompts (less secure)

### Behind Corporate Proxy
```ini
[tableau]
use_proxy = False
```
Use Windows system proxy (recommended)

### Custom Download Location
```ini
[tableau]
downloads_dir = D:/Tableau/Downloads
```

## Next Steps

1. ✅ **Run basic scraper** - `python get_tableau_stats.py`
2. ✅ **Check Excel output** - Look in Downloads folder
3. ✅ **Analyze data** - Use Polars for filtering/aggregation
4. ✅ **Automate** - Schedule script for regular runs

## Performance Tips

- **First run**: ~5-10 minutes for 10 workbooks with 50 views
- **Subsequent runs**: Use `refresh_data=False` to skip downloads
- **Headless mode**: Add to script: `scraper.setup_driver(headless=True)`
- **Large datasets**: Use Parquet format instead of CSV

## Need More Help?

- **Full Documentation**: See `README.md`
- **Stats Scraper Details**: See `STATS_SCRAPER_README.md`
- **R to Python Guide**: See `R_TO_PYTHON_CONVERSION.md`

## Quick Reference

| Task | Command |
|------|---------|
| Get all stats | `python get_tableau_stats.py` |
| Single view | `python test_scraper.py` |
| Fix ChromeDriver | `python fix_chromedriver.py` |
| Test Chrome | `python test_chrome_setup.py` |

---

**Ready to start!** Just run `python get_tableau_stats.py` 🚀

