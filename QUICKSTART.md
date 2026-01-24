# Quick Start Guide

## How to Run the App

### Option 1: Use the PowerShell script (easiest)

```powershell
.\run_app.ps1
```

### Option 2: Manual command

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Using Your URL List File

The app now supports **simple `.txt` files** with one YouTube URL per line (like `b2b_saas_YT_dataset.txt`).

### Steps:

1. **Start the app** (see above)

2. **Upload your file**:
   - Click "Browse files" in the upload area
   - Select `example_inputs/b2b_saas_YT_dataset.txt` (or your own `.txt` file)
   - The app will auto-detect it's a URL list and convert it

3. **Column mapping** (should auto-detect):
   - `source_type` → should show "source_type" 
   - `youtube_url` → should show "youtube_url"
   - Other fields can be "(none)"

4. **Preview**:
   - Check the preview table to see normalized rows
   - Should show all your URLs with `source_type=youtube`

5. **Click "Start session"**:
   - Creates a session folder in `output/sessions/`
   - Writes `items.csv` and `manifest.json`
   - ⚠️ **Note**: Transcript processing not yet implemented (see README)

## File Format Support

- **`.txt`** - Simple URL list (one per line, blank lines ignored)
- **`.csv`** - Spreadsheet with columns
- **`.tsv`** - Tab-separated values
- **`.xlsx`** - Excel file

## Troubleshooting

- **"Virtual environment not found"**: Run `python -m venv .venv` first
- **App won't start**: Make sure dependencies are installed: `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`
- **DEAPI warning**: This is OK for now - YouTube captions will still work
