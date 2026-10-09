from fastapi import APIRouter, HTTPException, Query
from app.db import get_client
from app.models.alerts import Alert, AlertUpdateStatus, AlertAssign
from typing import Optional
from uuid import UUID

router = APIRouter(prefix="/alerts",tags=["alerts"])

@router.get("",response_model=list[Alert])
async def list_alerts(
    #every 60 secs
    severity:Optional[str] = Query(None,description="Filter by severity"),
    status:Optional[str] = Query(None,description="Filter by status"),
    limit: int = Query(50,le=500)
):
    client = await get_client()
    conditions = []
    params = {}

    if severity:
        conditions.append("severity = {severity:String}")
        params["severity"] = severity
    if status:
        conditions.append("status = {status:String}")
        params["status"] = status

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    query = f"""
        SELECT id, timestamp, severity, category, mitre_technique,
               status, assigned_analyst, rule_name
        FROM alerts FINAL
        {where_clause}
        ORDER BY timestamp DESC
        LIMIT {limit}
    """
    result = await client.query(query,parameters=params)
    rows = result.result_rows
    columns = result.column_names

    return [dict(zip(columns, row)) for row in rows]

@router.get("/{alert_id}",response_model=Alert)
async def get_alert(alert_id:UUID):
    client = await get_client()

    query = """
        SELECT id, timestamp, severity, category, mitre_technique,
               status, assigned_analyst, rule_name
        FROM alerts FINAL
        WHERE id = {alert_id:UUID}
        LIMIT 1
    """
    result = await client.query(query,parameters={"alert_id": alert_id})

    if not result.result_rows:
        raise HTTPException(status_code=404, detail="Alert not found")
    return dict(zip(result.column_names,result.result_rows[0]))

async def _bump_alert(alert_id: UUID, replace: str, params: dict):
    # Copy the latest row with a higher version entirely inside ClickHouse.
    # Round-tripping DateTime64 columns through Python shifts them by the
    # local UTC offset on every update, so never re-insert fetched rows.
    client = await get_client()

    existing = await client.query(
        "SELECT 1 FROM alerts FINAL WHERE id = {id:UUID} LIMIT 1",
        parameters={"id": alert_id},
    )
    if not existing.result_rows:
        raise HTTPException(status_code=404, detail="Alert not found")

    await client.command(
        f"""
        INSERT INTO alerts
        SELECT * REPLACE ({replace}, version + 1 AS version, now64(3) AS updated_at)
        FROM alerts FINAL
        WHERE id = {{id:UUID}}
        """,
        parameters={"id": alert_id, **params},
    )

@router.patch("/{alert_id}/status")
async def update_alert_status(alert_id: UUID, body: AlertUpdateStatus):
    await _bump_alert(alert_id, "{status:String} AS status", {"status": body.status.value})
    return {"id": alert_id, "status": body.status.value}


@router.patch("/{alert_id}/assign")
async def assign_alert(alert_id: UUID, body: AlertAssign):
    await _bump_alert(alert_id, "{analyst:String} AS assigned_analyst", {"analyst": body.assigned_analyst})
    return {"id": alert_id, "assigned_analyst": body.assigned_analyst}
