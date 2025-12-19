"""API Client for Geek Magic."""
import asyncio
import socket
import aiohttp
import async_timeout
import random

import time
import logging
import re

_LOGGER = logging.getLogger(__name__)

class GeekMagicApiClient:
    """API Client for Geek Magic."""

    def __init__(self, session: aiohttp.ClientSession, url: str) -> None:
        """Initialize the API client."""
        self._session = session
        self._url = url.rstrip("/")
        self._theme = None
        self._brt = None
        self._free_space = None

    async def async_get_data(self) -> dict:
        """Get data from the API."""
        # Fetch both theme and brightness
        theme_data = await self._api_wrapper("get", "app.json")
        brt_data = await self._api_wrapper("get", "brt.json")
        
        if theme_data is not None:
            self._theme = theme_data.get("theme")
        if brt_data is not None:
            self._brt = brt_data.get("brt")
            
        return {
            "theme": self._theme,
            "brt": self._brt,
        }

    async def async_get_space(self) -> int | None:
        """Get free space in bytes."""
        data = await self._api_wrapper("get", "space.json")
        if data is not None:
            self._free_space = data.get("free")
        return self._free_space

    async def async_get_images(self) -> list[str]:
        """Get list of images."""
        # /filelist?dir=/image returns HTML
        # The device sends duplicate Content-Length headers which aiohttp rejects.
        # We use requests (via executor) as a workaround.
        loop = asyncio.get_running_loop()
        
        def _fetch():
            import requests
            resp = requests.get(
                f"{self._url}/filelist", 
                params={"dir": "/image"},
                timeout=10
            )
            resp.raise_for_status()
            return resp.text

        try:
             html = await loop.run_in_executor(None, _fetch)
        except Exception as err:
             _LOGGER.error("Error fetching images: %s", err)
             return []

        # Pattern: href='/image/1.gif' -> 1.gif
        matches = re.findall(r"href='/image/([^']+)'", html)
        return matches

    async def async_get_small_images(self) -> list[str]:
        """Get list of small (weather) images."""
        # /filelist?dir=/gif returns HTML
        # The device sends duplicate Content-Length headers which aiohttp rejects.
        # We use requests (via executor) as a workaround.
        loop = asyncio.get_running_loop()
        
        def _fetch():
            import requests
            resp = requests.get(
                f"{self._url}/filelist", 
                params={"dir": "/gif"},
                timeout=10
            )
            resp.raise_for_status()
            return resp.text

        try:
             html = await loop.run_in_executor(None, _fetch)
        except Exception as err:
             _LOGGER.error("Error fetching images: %s", err)
             return []

        # Pattern: href='/gif/1.gif' -> 1.gif
        matches = re.findall(r"href='/gif/([^']+)'", html)
        return matches

    async def async_set_theme(self, theme_id: int) -> None:
        """Set the theme."""
        await self._api_wrapper("get", "set", params={"theme": theme_id}, is_json=False)

    async def async_set_brightness(self, value: int) -> None:
        """Set the brightness."""
        await self._api_wrapper("get", "set", params={"brt": value}, is_json=False)

    async def async_set_image(self, filename: str) -> None:
        """Set the image."""
        # /set?img=/image/<filename>
        await self._api_wrapper("get", "set", params={"img": f"/image/{filename}"}, is_json=False)
        # Switch to theme 3 (Photo Album)
        await self.async_set_theme(3)

    async def async_set_small_image(self, filename: str) -> None:
        """Set the small (weather) image."""
        # /set?img=/gif/<filename>
        await self._api_wrapper("get", "set", params={"gif": f"/gif/{filename}"}, is_json=False)

    async def async_upload_file(self, file_data: bytes, filename: str) -> None:
        """Upload a file to the device."""
        # /doUpload?dir=/image/
        # The device sends duplicate Content-Length headers which aiohttp rejects.
        # We use requests (via executor) as a workaround.
        loop = asyncio.get_running_loop()

        def _upload():
            import requests
            # files argument for requests handles multipart
            files = {"file": (filename, file_data, "image/jpeg")}
            
            resp = requests.post(
                f"{self._url}/doUpload",
                params={"dir": "/image/"},
                files=files,
                timeout=20
            )
            if resp.status_code != 200:
                 _LOGGER.error("Upload failed: %s %s", resp.status_code, resp.text)
            resp.raise_for_status()

        await loop.run_in_executor(None, _upload)

    async def _api_wrapper(self, method: str, url: str, data: dict | aiohttp.FormData | None = None, params: dict | None = None, is_json: bool = True) -> dict | str:
        """Get information from the API."""
        if params is None:
            params = {}

        headers = {}
        request_kwargs = {
            "method": method,
            "url": f"{self._url}/{url}",
            "params": params,
        }

        if data is not None:
            if isinstance(data, dict):
                 headers["Content-type"] = "application/json; charset=UTF-8"
                 request_kwargs["json"] = data
            else:
                 # FormData or other types (like bytes, string), let aiohttp handle content-type
                 request_kwargs["data"] = data
        else:
             headers["Content-type"] = "application/json; charset=UTF-8"

        request_kwargs["headers"] = headers

        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(**request_kwargs)
                _LOGGER.debug("Requesting %s with params %s", f"{self._url}/{url}", params)
                
                if response.status == 404:
                    _LOGGER.info("404 received from %s, using last known value if available", f"{self._url}/{url}")
                    return None
                    
                response.raise_for_status()
                
                if is_json:
                    json_data = await response.json(content_type=None)
                    return json_data
                
                text_data = await response.text()
                return text_data

        except asyncio.TimeoutError as exception:
            raise Exception(f"Timeout error fetching information from {self._url} - {exception}") from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise Exception(f"Error fetching information from {self._url} - {exception}") from exception
        except Exception as exception:  # pylint: disable=broad-except
            raise Exception(f"Something really wrong happened! - {exception}") from exception
