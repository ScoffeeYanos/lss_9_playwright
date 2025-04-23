async def get_missing_text_string(page):
    return await page.query_selector('[id="missing_text"]')