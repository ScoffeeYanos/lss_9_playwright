import asyncio
import importlib
import bot.replacements
import re
import math
from collections import defaultdict
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
        print(f"\033[94mTASKS: Scheduler set\033[0m")


async def set_context(context):
    global _context
    _context = context
    if _log:
        print(f"\033[94mTASKS: Context set\033[0m")


async def set_page(page):
    global _page
    _page = page
    if _log:
        print(f"\033[94mTASKS: Page set\033[0m")


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
        print(f"\033[94mTASKS: Login comleted\033[0m")
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
                if len(id_split) == 3 and id_split[2].isdigit():
                    id_num = int(id_split[2])
                    mission_ids.append(id_num)
        print(f"\033[96mMissionIDs:{mission_ids}\033[0m")
        return mission_ids
    else:
        print(f"\033[91mTASKS.login missing Page\033[0m")


async def alert_vehicle(page, vehicle):
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


async def manage_alert(page, id, REPLACEMENTS,PERSONEL_FW,NAME_SETS):
    missing_vehicles = await missing_analyze(page,id,REPLACEMENTS,PERSONEL_FW,NAME_SETS)
    alert = True
    print(missing_vehicles)
    if missing_vehicles == -1:
        return
    for key,value in missing_vehicles.items():
        for _ in range(value):
            alert = await alert_vehicle(page, key)
        if not alert:
            break
    if alert:
        await page.click('#alert_btn')
        print(f"TASKS.manage_alert ALERTED")


async def manage_all_alerts():
    mission_ids = await get_alerts(red=True)
    page = await _context.new_page()
    REPLACEMENTS,PERSONEL_FW,NAME_SETS = get_replacements()
    for var in mission_ids:
        await manage_alert(page, var, REPLACEMENTS,PERSONEL_FW,NAME_SETS)
    await page.close()
    print(f"\033[96mTASKS: LOOP COMPLETED\033[0m")
    await asyncio.sleep(30)


def get_replacements():
    importlib.reload(bot.replacements)
    return bot.replacements.REPLACEMENTS,bot.replacements.PERSONNEL_FW,bot.replacements.NAME_SETS


async def missing_analyze(page,id,REPLACEMENTS,PERSONNEL_FW,NAME_SETS):
    await page.goto("https://www.leitstellenspiel.de/missions/" + str(id))
    missing = await page.query_selector('[id="missing_text"]')
    if not missing:
        raise RuntimeError(f"Missing element 'missing_text' on mission page {id}")
    if (await missing.get_attribute('style')) == 'display: none; ':
        alert = await alert_vehicle(page, "GEN")
        if not alert:
            return -1
        await page.click('#alert_btn')
        await page.goto(f"https://www.leitstellenspiel.de/missions/{id}/backalarmDriving")
        await asyncio.sleep(0.5)
        missing = await page.query_selector('[id="missing_text"]')
    if (await missing.get_attribute('style')) == 'display: none; ':
        raise RuntimeError(f"TASKS.missing_analyze: Missning Display not found")
    missing_vehicles = await missing.query_selector('[data-requirement-type="vehicles"]')
    missing_personnel = await missing.query_selector('[data-requirement-type="personnel"]')
    missing_other = await missing.query_selector('[data-requirement-type="other"]')
    if missing_vehicles:
        missing_vehicles = (await missing_vehicles.text_content()).split(":")[1].strip().split(",")
        missing_vehicles = [s.strip().replace("\xa0", " ") for s in missing_vehicles]
        missing_vehicles = [REPLACEMENTS.get(v, v) for v in missing_vehicles]
    else:
        missing_vehicles = []

    if missing_personnel:
        missing_personnel = (await missing_personnel.text_content()).split(":")[1].strip().split(",")
        missing_personnel = [s.strip().replace("\xa0", " ") for s in missing_personnel]
        missing_personnel = [REPLACEMENTS.get(v, v) for v in missing_personnel]
    else:
        missing_personnel = []

    if missing_other:
        missing_other = (await missing_other.text_content()).split(":")[1].strip().split(",")
        missing_other = [s.strip().replace("\xa0", " ") for s in missing_other]
        missing_other = [REPLACEMENTS.get(v, v) for v in missing_other]
    else:
        missing_other = []

    vehicles_pre = defaultdict(int)
    for entry in missing_vehicles:
        match = re.match(r"(\d+)\s*(.+)", entry)
        if match:
            value = int(match.group(1))
            label = match.group(2).strip()
            vehicles_pre[label] = vehicles_pre[label] + value

    vehicles = defaultdict(int)
    for key, label in NAME_SETS.items():
        total = sum(
            count for vkey, count in vehicles_pre.items() if key in vkey
        )
        vehicles[label] = vehicles[label] + total

    personnel = defaultdict(int)
    for entry in missing_personnel:
        match = re.match(r"(\d+)\s*(.+)", entry)
        if match:
            value = int(match.group(1))
            label = match.group(2)
            personnel[label] = value

    other = defaultdict(int)
    for entry in missing_other:
        match = re.match(r"(\d+)\s*(.+)", entry)
        if match:
            value = int(match.group(1))
            label = match.group(2)
            other[label] = value

    for key,label in personnel.items():
        if key == "Feuerwehrleute":
            count = sum( vehicles[name] * PERSONNEL_FW.get(name, PERSONNEL_FW.get("default",0)) for name in vehicles )
            if label > count:
                missing = label - count
                vehicles_to_send = math.ceil(missing/PERSONNEL_FW.get(PERSONNEL_FW.get("personnel_vehicle")))
                vehicles[PERSONNEL_FW.get("personnel_vehicle")] = vehicles[PERSONNEL_FW.get("personnel_vehicle")] + vehicles_to_send

    return vehicles