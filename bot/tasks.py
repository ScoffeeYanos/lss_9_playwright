import asyncio

_scheduler = None
_context = None
_page = None
_log = False
global mission_global


async def set_log(log):
    global _log
    _log = log


async def set_scheduler(scheduler):
    global _scheduler
    _scheduler = scheduler
    if _log:
        print(f"TASKS: Scheduler set")


async def set_context(context):
    global _context
    _context = context
    if _log:
        print(f"TASKS: Context set")


async def set_page(page):
    global _page
    _page = page
    if _log:
        print(f"TASKS: Page set")


async def login(mail, password):
    if _page:
        await _page.fill("#user_email", mail)
        if _log:
            print(f"TASKS.login filled Username")
        await _page.fill("#user_password", password)
        if _log:
            print(f"TASKS.login filled Password")
        await _page.click("#new_user > input")
        if _log:
            print(f"TASKS.login clicked Button")
    else:
        print(f"TASKS.login missing Page")


async def get_alerts(red=False, yellow=False, green=False):
    if _page:
        elements = await _page.query_selector_all('[class*="mission_panel_red"]')
        mission_ids = []
        for element in elements:
            id = await element.get_attribute("id")
            if id and id.startswith("mission_panel_"):
                id_split = id.split("_")
                print(id_split)
                if len(id_split) == 3 and id_split[2].isdigit():
                    id_num = int(id_split[2])
                    mission_ids.append(id_num)
        print(f"MissionIDs:{mission_ids}")
        return mission_ids
    else:
        print(f"TASKS.login missing Page")


async def alert_vehicle(page, vehicle):
    vehicle_button = await page.query_selector(f'[search_attribute*="{vehicle}"]')
    if not vehicle_button:
        print(f"TASKS.manage_alert vehicle_button not found: {vehicle}")
        return False
    vehicle_check = await vehicle_button.query_selector('[class*="label-success"]')
    if vehicle_check:
        await vehicle_button.click()
        print(f"TASKS.manage_alert selected vehicle: {vehicle}")
        return True

    else:
        return False


async def manage_alert(page, id):
    await page.goto("https://www.leitstellenspiel.de/missions/" + str(id))
    missing_sub = None
    missing = await page.query_selector('[id="missing_text"]')
    print(missing)
    missing_sub = await missing.query_selector('[data-requirement-type="vehicles"]')
    if not missing_sub:
        alert = await alert_vehicle(page, "GEN")
        if not alert:
            return
        await page.click('#alert_btn')
        await page.goto(f"https://www.leitstellenspiel.de/missions/{id}/backalarmDriving")
        print(f"TASKS.manage_alert GEN ALERTED")
        await asyncio.sleep(0.5)
        missing = await page.query_selector('[id="missing_text"]')
        print(missing)
        missing_sub = await missing.query_selector('[data-requirement-type="vehicles"]')
    missing_text = await missing_sub.text_content()
    print(missing_text)
    missing_text = missing_text.split(":")[1].strip()
    missing_text = missing_text.split(",")
    missing_text = [s.strip().replace("\xa0", " ") for s in missing_text]
    await asyncio.sleep(0.5)
    alert = True
    for vehicle in missing_text:
        if vehicle.startswith("Ein beliebiges Fahrzeug"):
            vehicle = "1 Löschfahrzeug"
        if not vehicle[0].isdigit():
            continue
        alert = await alert_vehicle(page, vehicle)
        if not alert:
            break
    if alert:
        await page.click('#alert_btn')
        print(f"TASKS.manage_alert ALERTED")


async def manage_all_alerts():
    mission_ids = await get_alerts(red=True)
    page = await _context.new_page()
    for var in mission_ids:
        await manage_alert(page, var)
    await page.close()
    print(f"scheduled")
    await asyncio.sleep(30)
    await manage_all_alerts()
