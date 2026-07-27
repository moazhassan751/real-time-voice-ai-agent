"""
Google Sheets tool — read ranges, append rows, and find spreadsheets by name.
"""

from googleapiclient.discovery import build

from google_auth import get_google_credentials


def _get_sheets_service():
    return build("sheets", "v4", credentials=get_google_credentials())


def _get_drive_service():
    return build("drive", "v3", credentials=get_google_credentials())


def find_spreadsheet_by_name(name: str) -> str:
    """Find a Google Sheets spreadsheet by name and return its ID.

    This is useful because spreadsheet IDs are not natural to say aloud.
    The LLM can call this first, then use the returned ID in follow-up
    ``read_range`` or ``append_row`` calls.

    Args:
        name: The spreadsheet name to search for.

    Returns the spreadsheet ID or a spoken error message.
    """
    try:
        service = _get_drive_service()
        q = (
            f"name contains '{name}' "
            f"and mimeType = 'application/vnd.google-apps.spreadsheet' "
            f"and trashed = false"
        )
        result = service.files().list(
            q=q,
            pageSize=1,
            fields="files(id, name)",
        ).execute()

        files = result.get("files", [])
        if not files:
            return f"I couldn't find a spreadsheet called '{name}' in your Drive."

        found = files[0]
        return (
            f"Found spreadsheet '{found['name']}' "
            f"with ID {found['id']}. You can use this ID to read or write data."
        )

    except Exception as e:
        return f"Sorry, I couldn't search for that spreadsheet. {e}"


def read_range(spreadsheet_id: str, range_name: str) -> str:
    """Read values from a Google Sheets range.

    Args:
        spreadsheet_id: The spreadsheet ID (from ``find_spreadsheet_by_name``).
        range_name: The A1-notation range (e.g. "Sheet1!A1:C10").

    Returns the values as a spoken-friendly summary.
    """
    try:
        service = _get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name,
        ).execute()

        values = result.get("values", [])
        if not values:
            return f"The range {range_name} is empty."

        # Summarize rows.
        row_count = len(values)
        col_count = max(len(row) for row in values) if values else 0

        # For small results, read the data aloud.
        if row_count <= 5:
            lines = []
            for i, row in enumerate(values, 1):
                cells = ", ".join(str(c) for c in row)
                lines.append(f"Row {i}: {cells}")
            return f"Here are {row_count} rows from {range_name}. " + ". ".join(lines) + "."

        # For larger results, just summarize.
        first_row = ", ".join(str(c) for c in values[0])
        return (
            f"The range {range_name} has {row_count} rows and {col_count} columns. "
            f"The first row is: {first_row}."
        )

    except Exception as e:
        return f"Sorry, I couldn't read that spreadsheet range. {e}"


def append_row(spreadsheet_id: str, range_name: str, values: list) -> str:
    """Append a row of values to a Google Sheet.

    Args:
        spreadsheet_id: The spreadsheet ID.
        range_name: The target range/sheet (e.g. "Sheet1").
        values: A list of cell values to append as a single row.

    Returns a spoken confirmation.
    """
    try:
        service = _get_sheets_service()
        body = {"values": [values]}
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body=body,
        ).execute()

        cell_summary = ", ".join(str(v) for v in values)
        return f"Done! I've appended a new row with values: {cell_summary}."

    except Exception as e:
        return f"Sorry, I couldn't append to that spreadsheet. {e}"


def create_spreadsheet(title: str, headers: list[str] = None) -> str:
    """Create a new Google Sheet via the Sheets API.

    Args:
        title: Title of the spreadsheet.
        headers: Optional list of column header strings (e.g. ["Date", "Item", "Cost"]).

    Returns a spoken confirmation string containing the real spreadsheet ID.
    """
    try:
        service = _get_sheets_service()
        spreadsheet_body = {
            "properties": {"title": title}
        }
        created = service.spreadsheets().create(
            body=spreadsheet_body,
            fields="spreadsheetId",
        ).execute()

        sheet_id = created.get("spreadsheetId", "")

        if headers:
            append_body = {"values": [headers]}
            service.spreadsheets().values().append(
                spreadsheetId=sheet_id,
                range="Sheet1",
                valueInputOption="USER_ENTERED",
                insertDataOption="INSERT_ROWS",
                body=append_body,
            ).execute()

        return (
            f"Done! Created a new Google Spreadsheet called '{title}' "
            f"with ID {sheet_id}."
        )
    except Exception as e:
        return f"Sorry, I couldn't create the spreadsheet. {e}"
