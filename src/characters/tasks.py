from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlmodel import select, func
from db import get_async_session
from helpers.third_party.lor_processor import LorFetcher
from helpers.third_party.schemas import LorFetcherOptions
from sqlmodel.ext.asyncio.session import AsyncSession
from characters.service import bulk_create_or_update_characters
from characters.models import LorCharacter
import logging
from helpers.redis import invalidate_characters_cache
logger = logging.getLogger(__name__)


async def check_lor_characters_exist(session: AsyncSession) -> bool:
    """Check if any records exist in the LorCharacter table."""
    statement = select(func.count(LorCharacter.id))
    result = await session.exec(statement)
    count = result.one()
    return count > 0


async def fetch_and_update(session: AsyncSession = None):
    """If session is not provided, create a new one"""
    local_session = False
    try:
        if session is None:
            async for new_session in get_async_session():
                session = new_session
                local_session = True
                break

        options = LorFetcherOptions(resourse="character")
        fetcher = LorFetcher()
        try:
            data = await fetcher.fetch_data(options)
        except Exception as api_error:
            logger.error(f"API fetch error: {str(api_error)}")
            return

        if not data:
            logger.warning("No data received from API")
            return

        docs = data.get("docs", [])

        if not docs:
            logger.warning("No characters data received from API")
            return

        updated_characters = await bulk_create_or_update_characters(session, docs)
        logger.info(f"Successfully processed {len(updated_characters)} characters")
        await invalidate_characters_cache()
    except Exception as e:
        logger.error(f"Error in fetch_and_update task: {str(e)}")
        raise
    finally:
        if local_session and session:
            await session.close()


def start_scheduler():
    scheduler = AsyncIOScheduler()

    async def initialize_data():
        """Check and initialize data if needed."""
        try:
            async for session in get_async_session():
                has_records = await check_lor_characters_exist(session)
                if not has_records:
                    logger.info(
                        "No LOR characters found in database. Running initial fetch..."
                    )
                    await fetch_and_update(session)
                    logger.info("Initial fetch completed")
                break
        except Exception as e:
            logger.error(f"Error during initial data check: {str(e)}")

    scheduler.add_job(initialize_data, "date")

    scheduler.add_job(
        fetch_and_update,
        "cron",
        hour=0,
        minute=0,
        misfire_grace_time=3600,
        coalesce=True,
        max_instances=1,
        id="fetch_and_update_characters",
    )

    scheduler.start()
    logger.info("Character fetch scheduler started")
