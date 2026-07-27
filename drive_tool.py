"""
Google Drive tool — search files, read content, create files.
"""

import io

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from google_auth import get_google_credentials


def _get_service():
    return build("drive", "v3", credentials=get_google_credentials())


def search_files(query: str, max_results: int = 5) -> str:
    """Search Google Drive for files matching *query* by name.

    Args:
        query: Search term to match against file names.
        max_results: Maximum number of results to return.

    Returns a spoken list of matching file names.
    """
    try:
        service = _get_service()
        q = f"name contains '{query}' and trashed = false"
        result = service.files().list(
            q=q,
            pageSize=max_results,
            fields="files(id, name, mimeType)",
        ).execute()

        files = result.get("files", [])
        if not files:
            return f"I didn't find any files matching '{query}' in your Drive."

        names = [f["name"] for f in files]
        if len(names) == 1:
            return f"I found one file: {names[0]}."

        if len(names) == 2:
            joined = f"{names[0]} and {names[1]}"
        else:
            joined = ", ".join(names[:-1]) + f", and {names[-1]}"
        return f"I found {len(names)} files: {joined}."

    except Exception as e:
        return f"Sorry, I couldn't search your Drive. {e}"


def read_file_content(file_name: str) -> str:
    """Find a file by name on Google Drive and return its text content.

    Handles Google Docs (via export) and plain text files (via download).

    Args:
        file_name: The name of the file to read.

    Returns the file's text content or a spoken error message.
    """
    try:
        service = _get_service()
        q = f"name = '{file_name}' and trashed = false"
        result = service.files().list(
            q=q,
            pageSize=1,
            fields="files(id, name, mimeType)",
        ).execute()

        files = result.get("files", [])
        if not files:
            return f"I couldn't find a file called '{file_name}' in your Drive."

        file_info = files[0]
        file_id = file_info["id"]
        mime = file_info.get("mimeType", "")

        # Google Docs → export as plain text.
        if "google-apps" in mime:
            response = service.files().export(
                fileId=file_id,
                mimeType="text/plain",
            ).execute()
            if isinstance(response, bytes):
                content = response.decode("utf-8", errors="replace")
            else:
                content = str(response)
        else:
            # Regular file → download content.
            response = service.files().get_media(fileId=file_id).execute()
            if isinstance(response, bytes):
                content = response.decode("utf-8", errors="replace")
            else:
                content = str(response)

        content = content.replace("\ufeff", "").strip()

        # Truncate very long content for spoken output.
        if len(content) > 2000:
            content = content[:2000] + "... (truncated)"

        return f"Here's the content of {file_name}: {content}"

    except Exception as e:
        return f"Sorry, I couldn't read that file. {e}"


def create_file(name: str, content: str) -> str:
    """Create a new Google Doc with the given name and text content.

    Args:
        name: Name/title of the new document.
        content: Text content to write into the document.

    Returns a spoken confirmation with the file link.
    """
    try:
        service = _get_service()

        file_metadata = {
            "name": name,
            "mimeType": "application/vnd.google-apps.document",
        }

        # Upload text content as a Google Doc.
        media = MediaIoBaseUpload(
            io.BytesIO(content.encode("utf-8")),
            mimetype="text/plain",
            resumable=False,
        )

        created = service.files().create(
            body=file_metadata,
            media_body=media,
            fields="id, webViewLink",
        ).execute()

        link = created.get("webViewLink", "")
        return f"Done! I've created a Google Doc called '{name}'. Link: {link}"

    except Exception as e:
        return f"Sorry, I couldn't create that file. {e}"
