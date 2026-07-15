from datetime import datetime, timedelta, timezone
from threading import Lock

import requests
from requests.auth import HTTPBasicAuth

from backend.config import get_settings


class EbayAPIError(Exception):
    pass


class EbayAuthenticationError(EbayAPIError):
    pass


class EbayAPIProvider:
    def __init__(self):
        self.settings = get_settings()
        self._token = self.settings.ebay_api_token
        self._token_expires_at = None
        self._token_lock = Lock()

    def _token_is_valid(self):
        if not self._token:
            return False
        if not self._token_expires_at:
            return True

        refresh_margin = timedelta(minutes=5)
        return datetime.now(timezone.utc) < self._token_expires_at - refresh_margin

    def _refresh_token(self):
        client_id = self.settings.ebay_client_id
        client_secret = self.settings.ebay_client_secret
        if not client_id or not client_secret:
            raise EbayAuthenticationError(
                "The eBay access token expired. Set EBAY_CLIENT_ID and "
                "EBAY_CLIENT_SECRET for automatic refresh, or replace EBAY_API_TOKEN."
            )

        try:
            response = requests.post(
                "https://api.ebay.com/identity/v1/oauth2/token",
                data={
                    "grant_type": "client_credentials",
                    "scope": "https://api.ebay.com/oauth/api_scope",
                },
                auth=HTTPBasicAuth(client_id, client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=self.settings.ebay_request_timeout,
            )
        except requests.Timeout as exc:
            raise EbayAPIError("Timed out while refreshing the eBay access token.") from exc
        except requests.RequestException as exc:
            raise EbayAPIError("Unable to refresh the eBay access token.") from exc

        if response.status_code == 401:
            raise EbayAuthenticationError("eBay rejected the configured client credentials.")
        try:
            response.raise_for_status()
        except requests.RequestException as exc:
            raise EbayAPIError("Unable to refresh the eBay access token.") from exc

        token_response = response.json()
        self._token = token_response.get("access_token")
        if not self._token:
            raise EbayAPIError("eBay's token response did not contain an access token.")

        expires_in = token_response.get("expires_in")
        if expires_in:
            try:
                self._token_expires_at = (
                    datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))
                )
            except (TypeError, ValueError):
                self._token_expires_at = None
        else:
            self._token_expires_at = None

        return self._token

    def _ensure_token(self):
        if self._token_is_valid():
            return self._token

        with self._token_lock:
            if not self._token_is_valid():
                return self._refresh_token()

        return self._token

    def _headers(self):
        self._ensure_token()
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json"
        }

    def _get(self, url, *, params=None):
        try:
            response = requests.get(
                url,
                params=params,
                headers=self._headers(),
                timeout=self.settings.ebay_request_timeout,
            )
        except requests.Timeout as exc:
            raise EbayAPIError("Timed out while calling the eBay API.") from exc
        except requests.RequestException as exc:
            raise EbayAPIError("Could not reach the eBay API.") from exc

        if response.status_code == 401:
            with self._token_lock:
                self._token = None
                self._token_expires_at = None
                self._refresh_token()
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=self._headers(),
                    timeout=self.settings.ebay_request_timeout,
                )
            except requests.Timeout as exc:
                raise EbayAPIError("Timed out while retrying the eBay API.") from exc
            except requests.RequestException as exc:
                raise EbayAPIError("Could not reach the eBay API during retry.") from exc

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
