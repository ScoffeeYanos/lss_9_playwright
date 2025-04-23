import asyncio
import importlib
import bot.replacements
import re
import math
import bot.subtasks
from collections import defaultdict

from bot.subtasks import *

REPLACEMENTS = {}
PERSONNEL_FW = {}
NAME_SETS = {}
WATER_FW = {}


async def refresh_imports():
    global REPLACEMENTS, PERSONNEL_FW, NAME_SETS, WATER_FW
    importlib.reload(bot.replacements)
    REPLACEMENTS = bot.replacements.REPLACEMENTS
    PERSONNEL_FW = bot.replacements.PERSONNEL_FW
    NAME_SETS = bot.replacements.NAME_SETS
    WATER_FW = bot.replacements.WATER_FW


async def login(page, mail, password):
    if page:
        await page.fill("#user_email", mail)
        await page.fill("#user_password", password)
        await page.click("#new_user > input")
        print(f"\033[94mTASKS: Login comleted\033[0m")
    else:
        print(f"TASKS.login missing Page")


async def manage_alert(page, id):
    await page.goto("https://www.leitstellenspiel.de/missions/" + str(id))
    missing_vehicles = await missing_analyze(page,await get_missing_text_string(page))
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


async def missing_analyze(page,missing):
    if not missing:
        raise RuntimeError(f"Missing element 'missing_text' on mission page {id}")
    if (await missing.get_attribute('style')) == 'display: none; ':
        alert = await alert_vehicle(page)
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


async def manage_all_alerts(context,mainpage,sleeptime = 30):
    await refresh_imports()
    mission_ids = await get_missions(mainpage,returnid=True)
    mission_page = await context.new_page()
    for mission_id in mission_ids:
        await manage_alert(mission_page, mission_id)
    await mission_page.close()
    print(f"\033[96mTASKS: LOOP COMPLETED\033[0m")
    await asyncio.sleep(sleeptime)
