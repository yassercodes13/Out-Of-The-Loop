import asyncio
import logging
from config import RETRY_SLEEP_SECONDS
from telegram.error import BadRequest, Forbidden, RetryAfter, NetworkError, ChatMigrated

logger = logging.getLogger(__name__)
async def retry_async(func, label):
  try:
    return await func()
  except NetworkError as e:
    logger.warning(f"{label} failed, retrying | error: {e}")
    await asyncio.sleep(RETRY_SLEEP_SECONDS)
    try:
      return await func()
    except NetworkError as e:
      logger.error(f"{label} failed after retry | error: {e}")
      raise
  except RetryAfter as e:
    wait = e.retry_after.total_seconds() if hasattr(e.retry_after, "total_seconds") else e.retry_after
    logger.warning(f"{label} failed, retrying after ({wait}) | error: {e}")
    await asyncio.sleep(wait)
    try:
      return await func()
    except RetryAfter as e:
      logger.error(f"{label} failed after retry | error: {e}")
      raise
  except (BadRequest, Forbidden, ChatMigrated) as e:
    logger.error(f"{label} failed | error: {e}")
    raise
