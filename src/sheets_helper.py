# sheets_helper.py
import pandas as pd
from typing import List
import gspread
from oauth2client.service_account import ServiceAccountCredentials


def read_profiles_csv(csv_path: str) -> List[str]:
    df = pd.read_csv(csv_path)
    if "prooflink" not in df.columns:
        raise ValueError("CSV must contain 'prooflink' column!")
    urls = df["prooflink"].astype(str).tolist()
    return urls


def read_profiles_gsheet(sheet_url: str, creds_file: str) -> List[str]:
    if gspread is None or ServiceAccountCredentials is None:
        raise ImportError("gspread / oauth2client is not installed or not available.")

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/drive.file",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_name(creds_file, scope)
    client = gspread.authorize(creds)

    sh = client.open_by_url(sheet_url)
    worksheet = sh.sheet1

    data = worksheet.get_all_values()
    if len(data) < 2:
        print("Empty table?")
        return []

    header = data[0]
    try:
        col_index = header.index("prooflink")
    except ValueError:
        raise ValueError("Column 'prooflink' not found in Google Sheets.")

    prooflinks = []
    for row in data[1:]:
        if len(row) > col_index:
            prooflinks.append(row[col_index])
    return prooflinks
