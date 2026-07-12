import requests
import os
from requests.auth import HTTPBasicAuth

from backend.config import load_project_env


class EbayAPIError(Exception):
    pass


class EbayAuthenticationError(EbayAPIError):
    pass


class EbayAPIProvider:
    def __init__(self):
        load_project_env()
        self._token = os.getenv("EBAY_API_TOKEN")

    def _refresh_token(self):
        client_id = os.getenv("EBAY_CLIENT_ID")
        client_secret = os.getenv("EBAY_CLIENT_SECRET")
        if not client_id or not client_secret:
            raise EbayAuthenticationError(
                "The eBay access token expired. Set EBAY_CLIENT_ID and "
                "EBAY_CLIENT_SECRET for automatic refresh, or replace EBAY_API_TOKEN."
            )

        response = requests.post(
            "https://api.ebay.com/identity/v1/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "scope": "https://api.ebay.com/oauth/api_scope",
            },
            auth=HTTPBasicAuth(client_id, client_secret),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )
        if response.status_code == 401:
            raise EbayAuthenticationError("eBay rejected the configured client credentials.")
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise EbayAPIError("Unable to refresh the eBay access token.") from exc

        self._token = response.json().get("access_token")
        if not self._token:
            raise EbayAPIError("eBay's token response did not contain an access token.")
        return self._token

    def _headers(self):
        if not self._token:
            self._refresh_token()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

    def _get(self, url, *, params=None):
        response = requests.get(
            url,
            params=params,
            headers=self._headers(),
            timeout=15,
        )
        if response.status_code == 401:
            self._refresh_token()
            response = requests.get(
                url,
                params=params,
                headers=self._headers(),
                timeout=15,
            )
        if response.status_code == 401:
            raise EbayAuthenticationError("eBay rejected the access token.")
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise EbayAPIError(f"eBay API request failed with status {response.status_code}.") from exc
        return response.json()

    def search(self, query):
        return self._get(
            "https://api.ebay.com/buy/browse/v1/item_summary/search",
            params={"q": query, "limit": 20},
        )

    def get_item(self, item_id):
        return self._get(
            f"https://api.ebay.com/buy/browse/v1/item/{item_id}",
            params={"fieldgroups": "PRODUCT"},
        )

    def get_item_by_legacy_id(self, legacy_item_id):
        return self._get(
            "https://api.ebay.com/buy/browse/v1/item/get_item_by_legacy_id",
            params={"legacy_item_id": legacy_item_id, "fieldgroups": "PRODUCT"},
        )
