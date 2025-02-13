from settings import settings
from helpers.third_party.abstraction import DataFetcher
from helpers.third_party.schemas import LorFetcherOptions

import aiohttp


class LorFetcher(DataFetcher):
    async def fetch_data(self, options: LorFetcherOptions):
        headers = {"Authorization": f"Bearer {settings.LOR_API_KEY}"}
        if not options:
            raise ValueError(" you must pass resourse name ")
        url = settings.LOR_API_BASE_URL + f"/{options.resourse}"
        if options.id:
            url += f"/{options.id}"
        if options.filters:
            url += "?"
            for key in options.filters:
                url += f"{key.key}{key.equality}{key.value}&&"
        async with aiohttp.ClientSession() as session:
            results = await self._call_api(session, url, headers)
        return results

    async def _call_api(self, session: aiohttp.ClientSession, url, headers):
        async with session.get(url, headers=headers) as response:
            return await response.json()
