"""
Minimal TED (Tenders Electronic Daily) Scraper
Uses the official TED Search API to retrieve European procurement notices
Documentation: https://docs.ted.europa.eu/api/latest/search.html
"""

import argparse
import json
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# TED Search API endpoint (no authentication required for published notices)
SEARCH_API_URL = "https://api.ted.europa.eu/v3/notices/search"

DEFAULT_TIMEOUT_S = 30
DEFAULT_QUERY = "publication-date >= today(-7) SORT BY publication-date DESC"


def _create_session() -> requests.Session:
    session = requests.Session()
    retry = Retry(
        total=5,
        connect=5,
        read=5,
        backoff_factor=0.5,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers.update({"Accept": "application/json", "User-Agent": "tenders-scrapping/1.0"})
    return session


def _extract_notices(search_response: dict | None) -> list[dict]:
    if not search_response or not isinstance(search_response, dict):
        return []
    # The API response shape may evolve; support a few common keys.
    for key in ("notices", "results", "content", "items"):
        value = search_response.get(key)
        if isinstance(value, list):
            return value
    return []


def search_tenders(
    query: str,
    fields: list[str] | None = None,
    limit: int = 100,
    page: int = 1,
    scope: str = "ACTIVE",
    pagination_mode: str = "PAGE_NUMBER",
    iteration_next_token: str | None = None,
    session: requests.Session | None = None,
) -> dict | None:
    """
    Search for tenders on TED
    
    Args:
        query: Expert search query (default "*" returns all)
        fields: List of fields to return (e.g., ["ND", "PD", "OJ"])
        limit: Maximum number of results per page
    
    Returns:
        Dictionary containing search results
    """
    if fields is None:
        fields = ["ND", "PD", "OJ", "CY", "AA"]  # Notice ID, Publication Date, OJ Series, Country, Award Authority
    
    payload: dict = {
        "query": query,
        "fields": fields,
        "page": page,
        "limit": limit,
        "scope": scope,
        "paginationMode": pagination_mode,
        "onlyLatestVersions": False,
        "checkQuerySyntax": False,
    }

    if pagination_mode == "ITERATION" and iteration_next_token:
        payload["iterationNextToken"] = iteration_next_token
    
    try:
        session = session or _create_session()
        response = session.post(SEARCH_API_URL, json=payload, timeout=DEFAULT_TIMEOUT_S)
        # When retries are exhausted, requests may still return a non-2xx response.
        if response.status_code >= 400:
            raise requests.HTTPError(f"{response.status_code} Error", response=response)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        detail = ""
        if hasattr(e, "response") and e.response is not None:
            try:
                detail = f"\nResponse: {e.response.text[:500]}"
            except Exception:
                detail = ""
        print(f"Error fetching data: {e}{detail}")
        return None

def get_notice_xml(notice_id):
    """
    Download individual notice in XML format
    
    Args:
        notice_id: Publication number (e.g., "123456-2024")
    
    Returns:
        XML content as string
    """
    xml_url = f"https://ted.europa.eu/en/notice/{notice_id}/xml"
    
    try:
        response = requests.get(xml_url, timeout=DEFAULT_TIMEOUT_S)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching XML for {notice_id}: {e}")
        return None

def main():
    """CLI entrypoint."""

    parser = argparse.ArgumentParser(description="Fetch tenders from TED Search API")
    parser.add_argument(
        "--query",
        default=DEFAULT_QUERY,
        help="TED expert query (default: last 7 days, newest first)",
    )
    parser.add_argument("--limit", type=int, default=10, help="Results per page (default: 10, max: 250)")
    parser.add_argument("--page", type=int, default=1, help="Page number (default: 1)")
    parser.add_argument(
        "--max-results",
        type=int,
        default=0,
        help="If set, fetch multiple pages until this many notices are collected",
    )
    parser.add_argument("--scope", default="ACTIVE", help="Search scope (default: ACTIVE)")
    parser.add_argument("--json-out", default="", help="If set, write notices JSON to this file")
    parser.add_argument("--download-xml", action="store_true", help="Download XML for the first notice")
    args = parser.parse_args()

    print("Fetching tenders from TED...\n")
    session = _create_session()
    notices: list[dict] = []
    current_page = max(1, args.page)
    target = args.max_results if args.max_results and args.max_results > 0 else args.limit

    while len(notices) < target:
        results = search_tenders(
            query=args.query,
            limit=min(args.limit, 250),
            page=current_page,
            scope=args.scope,
            session=session,
        )
        page_notices = _extract_notices(results)
        if not page_notices:
            break

        notices.extend(page_notices)
        if args.max_results and len(notices) >= args.max_results:
            notices = notices[: args.max_results]
            break

        # Only fetch one page unless multi-page collection requested.
        if not args.max_results:
            break
        current_page += 1

    if notices:
        total = "N/A"
        if isinstance(results, dict):
            total = results.get("totalNoticeCount", results.get("total", results.get("totalCount", "N/A")))
        print(f"Total notices found: {total}")
        print(f"Showing {len(notices)} notices:\n")

        for notice in notices:
            print(f"Notice ID: {notice.get('ND', notice.get('publication-number', 'N/A'))}")
            print(f"Publication Date: {notice.get('PD', notice.get('publication-date', 'N/A'))}")
            print(f"Country: {notice.get('CY', notice.get('buyer-country', 'N/A'))}")
            print(f"OJ Series: {notice.get('OJ', notice.get('ojs-number', 'N/A'))}")
            print("-" * 50)

        if args.download_xml:
            first_notice_id = notices[0].get("ND")
            if first_notice_id:
                print(f"\nDownloading XML for notice {first_notice_id}...")
                xml_content = get_notice_xml(first_notice_id)
                if xml_content:
                    print(f"Successfully downloaded XML ({len(xml_content)} bytes)")

        if args.json_out:
            with open(args.json_out, "w", encoding="utf-8") as f:
                json.dump(notices, f, ensure_ascii=False, indent=2)
            print(f"\nWrote {len(notices)} notices to {args.json_out}")
    else:
        print("No results found or error occurred")

if __name__ == "__main__":
    main()