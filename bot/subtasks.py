async def get_missing_text_string(page):
    """

    :param page: Page to operate on. Needs to be opened on a direct alert page
    :return: Return The complete missing Text
    """
    return await page.query_selector('[id="missing_text"]')


async def get_missions(page, red:bool=False, yellow:bool=False, green:bool=False, timedlimit:int=600_000, returnid:bool=False):
    """

    :param page: Page to operate on. Needs to be opened main window or on alert list window
    :param red: include red alerts
    :param yellow: include red alerts
    :param green: include red alerts
    :param timedlimit: set timed missions max time value
    :param returnid: return only id of elements
    :return:
    """
    mission_elements = []
    if red:
        mission_elements.append(await page.query_selector_all('[class*="mission_panel_red"]'))
    if yellow:
        mission_elements.append(await page.query_selector_all('[class*="mission_panel_yellow"]'))
    if green:
        mission_elements.append(await page.query_selector_all('[class*="mission_panel_green]'))
    mission_elements = [element for element in mission_elements if
                        int(await (await element.query_selector('[class*="mission_overview_countdown"]')).get_attribute(
                            "timeleft")) <= timedlimit]  ##TODO check for timedlimit in non timed missions
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


async def alert_vehicle(page, vehicle:str="GEN"):
    vehicle_button = await page.query_selector(f'[search_attribute*="{vehicle}"]')
    if not vehicle_button:
        print(f"\033[95mTASKS.manage_alert vehicle_button not found: {vehicle}\033[0m")
        return False
    vehicle_check = await vehicle_button.query_selector('[class*="label-success"]')
    if vehicle_check:
        await vehicle_button.click()
        print(f"TASKS.manage_alert selected vehicle: {vehicle}")
        return True
    else:
        return False
