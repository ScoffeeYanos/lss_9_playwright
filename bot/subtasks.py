async def get_missing_text_string(page):
    return await page.query_selector('[id="missing_text"]')

async def get_missions(page,red = False,yellow = False,green = False,timedlimit = 600_000,returnid=False):
    mission_elements = []
    if  red:
        mission_elements.append(await page.query_selector_all('[class*="mission_panel_red"]'))
    if yellow:
        mission_elements.append(await page.query_selector_all('[class*="mission_panel_yellow"]'))
    if green:
        mission_elements.append(await page.query_selector_all('[class*="mission_panel_green]'))
    mission_elements = [element for element in mission_elements if int(await (await element.query_selector('[class*="mission_overview_countdown"]')).get_attribute("timeleft")) <= timedlimit]##TODO check for timedlimit in non timed missions
    if returnid:
        mission_ids = []
        for element in mission_elements:
            mission_id = await element.get_attribute("mission_id")
            if mission_id and mission_id.startswith("mission_panel_"):
                id_split = mission_id.split("_")
                if len(id_split) == 3 and id_split[2].isdigit():
                    mission_ids.append(int(id_split[2]))
    else:
        return mission_elements