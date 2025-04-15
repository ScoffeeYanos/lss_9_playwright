from playwright.async_api import async_playwright


class PlaywrightManager:
    def __init__(self, log=False):
        self.browser = None
        self.page = None
        self.context = None
        self.playwright = None
        self.log = log

    async def start(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        if self.log:
            print(f"MANAGER start complete")
        await self.page.goto("https://www.leitstellenspiel.de/users/sign_in")
        if self.log:
            print(f"MANAGER page load complete")

    async def stop(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
