import asyncio

from playwright.async_api import async_playwright

import bot
from bot.login import *
from bot import tasks
from bot.manager import PlaywrightManager
from bot.scheduler import AsyncScheduler


async def main():
    bot = PlaywrightManager(log=True)
    await bot.start()
    await tasks.set_log(True)
    await tasks.set_context(bot.context)
    await tasks.set_page(bot.page)
    scheduler = AsyncScheduler()
    scheduler.start()
    await tasks.set_scheduler(scheduler)
    await tasks.login(LG, PW)
    await asyncio.sleep(3)
    print(await tasks.get_alerts())
    await tasks.manage_all_alerts()
    await asyncio.sleep(60)


if __name__ == "__main__":
    asyncio.run(main())
