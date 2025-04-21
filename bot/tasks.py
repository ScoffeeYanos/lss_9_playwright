import asyncio
import importlib
import bot.replacements
import re
import math
from collections import defaultdict

_context = None
_page = None

REPLACEMENTS = {}
PERSONNEL_FW = {}
NAME_SETS = {}
WATER_FW = {}


async def set_context(context):
    global _context
    _context = context


async def set_page(page):
    global _page
    _page = page


async def login(mail, password):
    if _page:
        await _page.fill("#user_email", mail)
        await _page.fill("#user_password", password)
        await _page.click("#new_user > input")
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
                    if int(await (await element.query_selector('[class*="mission_overview_countdown"]')).get_attribute("timeleft")) <= 600000:
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


async def manage_alert(page, id):
    await page.reload()
    missing_vehicles = await missing_analyze(page, id)
    alert = True
    print(missing_vehicles)
    if missing_vehicles == -1:
        return
    for key, value in missing_vehicles.items():
        for _ in range(value):
            alert = await alert_vehicle(page, key)
        if not alert:
            break
    if alert:
        await page.click('#alert_btn')
        print(f"TASKS.manage_alert ALERTED")


async def manage_all_alerts():
    global REPLACEMENTS, PERSONNEL_FW, NAME_SETS, WATER_FW
    importlib.reload(bot.replacements)
    REPLACEMENTS = bot.replacements.REPLACEMENTS
    PERSONNEL_FW = bot.replacements.PERSONNEL_FW
    NAME_SETS = bot.replacements.NAME_SETS
    WATER_FW = bot.replacements.WATER_FW

    mission_ids = await get_alerts(red=True)
    page = await _context.new_page()
    for var in mission_ids:
        await manage_alert(page, var)
    await page.close()
    print(f"\033[96mTASKS: LOOP COMPLETED\033[0m")
    await asyncio.sleep(30)


async def missing_analyze(page, id):
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

    async def parse_missing_block(el, replacements):
        if not el:
            return []
        text = (await el.text_content()).split(":")[1].strip().split(",")
        return [replacements.get(s.strip().replace("\xa0", " "), s.strip().replace("\xa0", " ")) for s in text]

    missing_vehicles = await parse_missing_block(missing_vehicles, REPLACEMENTS)
    missing_personnel = await parse_missing_block(missing_personnel, REPLACEMENTS)
    missing_other = await parse_missing_block(missing_other, REPLACEMENTS)
    print(missing_vehicles)
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

    for key, label in personnel.items():
        if key == "Feuerwehrleute" or key == "Feuerwehrmann":
            count = sum(vehicles[name] * PERSONNEL_FW.get(name, PERSONNEL_FW.get("default", 0)) for name in vehicles)
            if label > count:
                missing = label - count
                vehicles_to_send = math.ceil(missing / PERSONNEL_FW.get(PERSONNEL_FW.get("personnel_vehicle")))
                vehicles[PERSONNEL_FW.get("personnel_vehicle")] = vehicles[PERSONNEL_FW.get("personnel_vehicle")] + vehicles_to_send

    for key, label in other.items():
        if key == "l. Wasser":
            count = sum(vehicles[name] * WATER_FW.get(name, WATER_FW.get("default", 0)) for name in vehicles)
            if label > count:
                missing = label - count
                vehicles_to_send = math.ceil(missing / WATER_FW.get(WATER_FW.get("water_vehicle")))
                vehicles[PERSONNEL_FW.get("water_vehicle")] = vehicles[PERSONNEL_FW.get("water_vehicle")] + vehicles_to_send

    return vehicles
