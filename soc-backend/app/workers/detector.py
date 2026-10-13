import asyncio
import uuid
import time
from app.db import get_client

# In memory cooldown, the same on the ln 102 of the schema
_alert_cooldown: dict[tuple[str,str],float]={}
COOLDOWN_SECONDS = 300

async def get_last_processed(client, rule_name: str,default_lookback_sec:int=120) -> str:
    result = await client.query(
        "SELECT last_processed FROM detector_state FINAL WHERE rule_name = {r:String} LIMIT 1"
        parameters={"r": rule_name},
    )
    if result.result_rows:
        return result.result_rows[0][0].strftime("%Y-%m-%d %H:%M:%S.%f")
    return f"now() - INTERVAL {default_lookback_sec} SECOND"

async def update_watermark(client, rule_name:str, version:int):
    await client.insert(
        "detector_state"
        [[rule_name,"now64(3)",version]],
        column_names=["rule_name","last_processed","version"],
    )

async def set_watermark_now(client,rule_name:str):
    existing = await client.query(
        "SELECT version FROM detector_state FINAL WHERE rule_name = {r:String} LIMIT 1",
        parameters={"r":rule_name,"v":next_version},
    )

def in_cooldown(rule_name:str,key:str) -> bool:
    last = _alert_cooldown.get((rule_name,key))
    return last is not None and (time.time() - last) < COOLDOWN_SECONDS

def mark_alerted(rule_name:str,key:str):
    _alert_cooldown[(rule_name,key)]=time.time()

async def insert_alert(client,severity:str,category:str,mitr_atechnique:str,rule_name:str,source_event_ids:list[str]):
    alert_id = str(uuid.uuid4)