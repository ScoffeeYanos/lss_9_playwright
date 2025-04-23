import asyncio
from playwright.async_api import async_playwright

from bot import tasks


async def main():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    context = await browser.new_context()
    page = await context.new_page()
    await page.goto("https://www.leitstellenspiel.de/users/sign_in")
    await tasks.login(LG, PW)
    while True:
        await tasks.manage_all_alerts(context,page)

if __name__ == "__main__":
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
