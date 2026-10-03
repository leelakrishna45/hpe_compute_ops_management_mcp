"""
HTTP client for HPE Compute Ops Management REST APIs.

This module provides a reusable asynchronous HTTP client used
by the MCP tools to communicate with HPE Compute Ops Management
through the HPE GreenLake API gateway.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx

from ..config import Settings, get_settings
from .auth import HPEAuth
from .exceptions import (
    HPEAPIError,
    HPEAuthenticationError,
    HPEAuthorizationError,
    HPEBadRequestError,
    HPEConnectionError,
    HPETimeoutError,
    HPENotFoundError,
    HPERateLimitError,
    HPEServerError,
)


class HPEComputeOpsClient:
    """
    Asynchronous HTTP client for HPE Compute Ops Management.

    Responsibilities:

    - Build HPE API URLs
    - Add authentication headers
    - Execute HTTP requests
    - Handle transient failures
    - Handle HPE API errors
    - Parse JSON responses
    - Provide a common interface to MCP tools
    """

    def __init__(
        self,
        settings: Settings | None = None,
    ) -> None:
        self.settings = (
            settings
            if settings is not None
            else get_settings()
        )

        self.auth = HPEAuth(
            self.settings
        )

        self.base_url = (
            self.settings
            .hpe_greenlake_api_base_url
            .rstrip("/")
        )

        self.timeout = (
            self.settings.http_timeout
        )

        self.max_retries = (
            self.settings.http_max_retries
        )

        self._client: httpx.AsyncClient | None = None

    # =========================================================
    # HTTP client lifecycle
    # =========================================================

    async def _get_client(self) -> httpx.AsyncClient:
        """
        Return the reusable HTTP client.

        A single AsyncClient is reused for multiple requests so
        that HTTP connections can be reused efficiently.
        """

        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
            )

        return self._client

    async def close(self) -> None:
        """
        Close the underlying HTTP client.
        """

        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def __aenter__(
        self,
    ) -> HPEComputeOpsClient:
        """
        Support async context manager usage.
        """

        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> None:
        """
        Close the HTTP client when leaving the context manager.
        """

        await self.close()

    # =========================================================
    # URL handling
    # =========================================================

    def _build_url(
        self,
        path: str,
    ) -> str:
        """
        Build a complete HPE API URL.

        Args:
            path:
                API path such as:

                /compute-ops-mgmt/v1beta1/servers

        Returns:
            Fully qualified URL.
        """

        if not path.startswith("/"):
            path = f"/{path}"

        return f"{self.base_url}{path}"

    # =========================================================
    # Headers
    # =========================================================

    def _build_headers(
        self,
        additional_headers: dict[str, str] | None = None,
    ) -> dict[str, str]:
        """
        Build HTTP headers for an HPE API request.
        """

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        headers.update(
            self.auth.get_auth_headers()
        )

        if additional_headers:
            headers.update(
                additional_headers
            )

        return headers

    # =========================================================
    # Retry handling
    # =========================================================

    @staticmethod
    def _get_retry_after(
        response: httpx.Response,
    ) -> int | None:
        """
        Extract Retry-After from an HTTP response.

        HPE/API gateways may provide Retry-After when a request
        has been rate limited.

        Returns:
            Number of seconds to wait, if available.
        """

        value = response.headers.get(
            "Retry-After"
        )

        if value is None:
            return None

        try:
            return int(value)

        except ValueError:
            return None

    @staticmethod
    def _get_retry_delay(
        attempt: int,
    ) -> float:
        """
        Calculate exponential backoff delay.

        Example:

        attempt 0 -> 1 second
        attempt 1 -> 2 seconds
        attempt 2 -> 4 seconds
        """

        return float(
            min(
                2**attempt,
                30,
            )
        )

    # =========================================================
    # Error response extraction
    # =========================================================

    @staticmethod
    def _extract_error_response(
        response: httpx.Response,
    ) -> Any:
        """
        Extract useful error information from an HPE response.
        """

        try:
            return response.json()

        except ValueError:
            return response.text

    # =========================================================
    # Error handling
    # =========================================================

    async def _raise_for_status(
        self,
        response: httpx.Response,
    ) -> None:
        """
        Convert HTTP failures into project-specific exceptions.
        """

        if response.status_code < 400:
            return

        details = self._extract_error_response(
            response
        )

        message = (
            "HPE Compute Ops Management API "
            f"returned HTTP {response.status_code}"
        )

        if details:
            message = (
                f"{message}: {details}"
            )

        # -----------------------------------------------------
        # 400 Bad Request
        # -----------------------------------------------------

        if response.status_code == 400:
            raise HPEBadRequestError(
                message,
                status_code=400,
                response=details,
            )

        # -----------------------------------------------------
        # 401 Unauthorized
        # -----------------------------------------------------

        if response.status_code == 401:
            raise HPEAuthenticationError(
                message,
                status_code=401,
                response=details,
            )

        # -----------------------------------------------------
        # 403 Forbidden
        # -----------------------------------------------------

        if response.status_code == 403:
            raise HPEAuthorizationError(
                message,
                status_code=403,
                response=details,
            )

        # -----------------------------------------------------
        # 404 Not Found
        # -----------------------------------------------------

        if response.status_code == 404:
            raise HPENotFoundError(
                message,
                status_code=404,
                response=details,
            )

        # -----------------------------------------------------
        # 429 Too Many Requests
        # -----------------------------------------------------

        if response.status_code == 429:
            retry_after = self._get_retry_after(
                response
            )

            raise HPERateLimitError(
                message,
                status_code=429,
                response=details,
                retry_after=retry_after,
            )

        # -----------------------------------------------------
        # 5xx Server Errors
        # -----------------------------------------------------

        if response.status_code >= 500:
            raise HPEServerError(
                message,
                status_code=response.status_code,
                response=details,
            )

        # -----------------------------------------------------
        # Other API errors
        # -----------------------------------------------------

        raise HPEAPIError(
            message,
            status_code=response.status_code,
            response=details,
        )

    # =========================================================
    # Response parsing
    # =========================================================

    @staticmethod
    async def _parse_response(
        response: httpx.Response,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Parse an HPE API response.

        Returns:
            Parsed JSON response.

        Raises:
            HPEAPIError:
                If the response contains invalid JSON.
        """

        if response.status_code == 204:
            return None

        if not response.content:
            return None

        try:
            return response.json()

        except ValueError as exc:

            raise HPEAPIError(
                "HPE Compute Ops Management returned "
                "an invalid JSON response.",
                status_code=response.status_code,
                response=response.text,
            ) from exc

    # =========================================================
    # Generic request
    # =========================================================

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | list[Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Execute an HTTP request against HPE Compute Ops
        Management.

        Retries are performed for:

        - HTTP 429
        - HTTP 5xx
        - Network errors
        - Timeouts

        Authentication and authorization failures are not
        retried.
        """

        url = self._build_url(
            path
        )

        request_headers = self._build_headers(
            headers
        )

        last_exception: Exception | None = None

        for attempt in range(
            self.max_retries + 1
        ):

            try:

                client = await self._get_client()

                response = await client.request(
                    method=method,
                    url=url,
                    headers=request_headers,
                    params=params,
                    json=json,
                )

                # -------------------------------------------------
                # Rate limiting
                # -------------------------------------------------

                if response.status_code == 429:

                    retry_after = (
                        self._get_retry_after(
                            response
                        )
                    )

                    if attempt < self.max_retries:

                        delay = (
                            float(retry_after)
                            if retry_after is not None
                            else self._get_retry_delay(
                                attempt
                            )
                        )

                        await asyncio.sleep(
                            delay
                        )

                        continue

                # -------------------------------------------------
                # Server-side errors
                # -------------------------------------------------

                if (
                    response.status_code >= 500
                    and attempt < self.max_retries
                ):

                    delay = (
                        self._get_retry_delay(
                            attempt
                        )
                    )

                    await asyncio.sleep(
                        delay
                    )

                    continue

                # -------------------------------------------------
                # Convert HTTP errors
                # -------------------------------------------------

                await self._raise_for_status(
                    response
                )

                # -------------------------------------------------
                # Parse successful response
                # -------------------------------------------------

                return await self._parse_response(
                    response
                )

            # -----------------------------------------------------
            # Timeout
            # -----------------------------------------------------

            except httpx.TimeoutException as exc:

                last_exception = exc

                if attempt < self.max_retries:

                    delay = (
                        self._get_retry_delay(
                            attempt
                        )
                    )

                    await asyncio.sleep(
                        delay
                    )

                    continue

                raise HPETimeoutError(
                    "Request to HPE Compute Ops Management "
                    f"timed out after {self.timeout} seconds."
                ) from exc

            # -----------------------------------------------------
            # Network / connection error
            # -----------------------------------------------------

            except httpx.RequestError as exc:

                last_exception = exc

                if attempt < self.max_retries:

                    delay = (
                        self._get_retry_delay(
                            attempt
                        )
                    )

                    await asyncio.sleep(
                        delay
                    )

                    continue

                raise HPEConnectionError(
                    "Unable to connect to HPE Compute Ops "
                    f"Management: {exc}"
                ) from exc

        # ---------------------------------------------------------
        # Defensive fallback
        # ---------------------------------------------------------

        raise HPEAPIError(
            "HPE Compute Ops Management request failed "
            "after all retry attempts."
        ) from last_exception

    # =========================================================
    # GET
    # =========================================================

    async def get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Execute an asynchronous GET request.
        """

        return await self._request(
            "GET",
            path,
            params=params,
            headers=headers,
        )

    # =========================================================
    # POST
    # =========================================================

    async def post(
        self,
        path: str,
        json: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Execute an asynchronous POST request.
        """

        return await self._request(
            "POST",
            path,
            params=params,
            json=json,
            headers=headers,
        )

    # =========================================================
    # PATCH
    # =========================================================

    async def patch(
        self,
        path: str,
        json: dict[str, Any] | list[Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Execute an asynchronous PATCH request.
        """

        return await self._request(
            "PATCH",
            path,
            params=params,
            json=json,
            headers=headers,
        )

    # =========================================================
    # DELETE
    # =========================================================

    async def delete(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any] | list[Any] | None:
        """
        Execute an asynchronous DELETE request.
        """

        return await self._request(
            "DELETE",
            path,
            params=params,
            headers=headers,
        )