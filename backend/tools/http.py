import os
import json
import requests
import logging
import aiohttp
from aiohttp import ClientTimeout
import random
from typing import List, Dict
from collections import defaultdict

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

logger = logging.getLogger(__name__)

HELIUS_API_KEY = os.getenv("HELIUS_API_KEY")
MAX_RETRIES = 10
BASE_WAIT = 1
MAX_WAIT = 60
MAX_FAILURES = 3  # Maximum number of failures before a proxy is considered bad


class RateLimitException(Exception):
    pass


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=BASE_WAIT, max=MAX_WAIT),
    retry=retry_if_exception_type(RateLimitException),
    reraise=True,
)
async def req_get(
    url: str,
    *,
    headers: dict = {},
    params: dict = {},
    helius_auth: bool = False,
    timeout: int = 5,
) -> Dict:
    timeout = ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        if helius_auth:
            params = {**params, "api-key": HELIUS_API_KEY}

        while True:
            try:
                async with session.get(url, headers=headers, params=params) as response:
                    if response.status == 429:  # Too Many Requests
                        response_text = await response.text()
                        logger.warning(
                            f"Rate limit exceeded for {url} with response {response_text}"
                        )
                        raise RateLimitException("Rate limit exceeded")

                    # Raise an error if the response is not ok
                    response.raise_for_status()

                    return await response.json()
            except RateLimitException:
                continue
            except Exception as e:
                logger.warning(f"Request failed: {str(e)}")
                raise


@retry(
    stop=stop_after_attempt(MAX_RETRIES),
    wait=wait_exponential(multiplier=BASE_WAIT, max=MAX_WAIT),
    retry=retry_if_exception_type(RateLimitException),
    reraise=True,
)
async def req_post(
    url: str,
    data: dict,
    *,
    headers: dict = {},
    params: dict = {},
    helius_auth: bool = False,
):
    async with aiohttp.ClientSession() as session:
        if helius_auth:
            params = {**params, "api-key": HELIUS_API_KEY}
        async with session.post(
            url, headers=headers, json=data, params=params
        ) as response:
            if response.status == 429:  # Too Many Requests
                response_text = await response.text()
                logger.warning(
                    "Rate limit exceeded for %s with data %s with response %s",
                    url,
                    data,
                    response_text,
                )
                raise RateLimitException("Rate limit exceeded")

            # Raise an error if the response is not ok
            response.raise_for_status()

            return await response.json()


async def req_put(
    url: str,
    data: dict,
    *,
    headers: dict = {},
    params: dict = {},
    helius_auth: bool = False,
    timeout: int = 5,
):
    timeout = ClientTimeout(total=timeout)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        if helius_auth:
            params = {**params, "api-key": HELIUS_API_KEY}

        try:
            async with session.put(
                url, headers=headers, json=data, params=params
            ) as response:
                # Raise an error if the response is not ok
                response.raise_for_status()

                return await response.json()
        except Exception as e:
            logger.warning(f"PUT request failed: {str(e)}")
            raise
