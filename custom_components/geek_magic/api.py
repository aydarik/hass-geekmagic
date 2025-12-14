"""API Client for Geek Magic."""
import asyncio
import socket
import aiohttp
import async_timeout
import random
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

    async def async_get_data(self) -> dict:
        """Get data from the API."""
        # Fetch both theme and brightness in parallel could be better,
        # but for simplicity and error handling let's do sequential for now or gather.
        # However, the requirement says: 
        # get values from <urs>/app.json | jq -r '.theme'
        # get values from <urs>/brt.json | jq -r '.brt'
        
        theme_data = await self._api_wrapper("get", "app.json")
        brt_data = await self._api_wrapper("get", "brt.json")
        
        return {
            "theme": theme_data.get("theme"),
            "brt": brt_data.get("brt"),
        }

    async def async_get_space(self) -> int | None:
        """Get free space in bytes."""
        data = await self._api_wrapper("get", "space.json")
        return data.get("free")

    async def async_get_images(self) -> list[str]:
        """Get list of images."""
        # /filelist?dir=/image/ returns HTML
        # The device sends duplicate Content-Length headers which aiohttp rejects.
        # We use requests (via executor) as a workaround.
        loop = asyncio.get_running_loop()
        
        def _fetch():
            import requests
            resp = requests.get(
                f"{self._url}/filelist", 
                params={"dir": "/image/", "_": int(time.time() * 1000) + random.randint(0, 1000)},
                timeout=10
            )
            resp.raise_for_status()
            return resp.text

        try:
             html = await loop.run_in_executor(None, _fetch)
        except Exception as err:
             _LOGGER.error("Error fetching images: %s", err)
             return []

        # Pattern: href='/image//1.gif' -> 1.gif
        # Note: User example shows /image//filename.gif
        matches = re.findall(r"href='/image//([^']+)'", html)
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

    async def _api_wrapper(self, method: str, url: str, data: dict | None = None, params: dict | None = None, is_json: bool = True) -> dict | str:
        """Get information from the API."""
        if params is None:
            params = {}
        params["_"] = int(time.time() * 1000) + random.randint(0, 1000)

        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=f"{self._url}/{url}",
                    headers={"Content-type": "application/json; charset=UTF-8"},
                    json=data,
                    params=params,
                )
                _LOGGER.debug("Requesting %s with params %s", f"{self._url}/{url}", params)
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
