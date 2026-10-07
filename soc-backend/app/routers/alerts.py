from fastapi import APIRouter, HTTPException, Query
from app.db import get_client
from app.models.alerts import Alert, AlertUpdateStatus, AlertAssign
from typing import Optional

router = APIRouter(prefix="/alerts",tags=["alerts"])

@router.get("",response_model=list[Alert])
async def list_alerts(
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
async def get_alert(alert_id:str):
    client = await get_client()

    query = """
        SELECT id, timestamp, severity, category, mitre_technique,
               status, assigned_analyst, rule_name
        FROM alerts FINAL
        WHERE id = {alert_id:String}
        LIMIT 1
    """
    result = await client.query(query,parameters={alert_id:alert_id})

    if not result.result_rows:
        raise HTTPException(status_code=404, detail="Alert not found")
    return dict(zip(result.column_names,result.result_rows[0]))

@router.patch("/{alert_id}/status")
async def update_alert_status(alert_id: str, body: AlertUpdateStatus):
  
    client = await get_client()

    existing = await client.query(
        "SELECT * FROM alerts FINAL WHERE id = {id:String} LIMIT 1",
        parameters={"id": alert_id},
    )
    if not existing.result_rows:
        raise HTTPException(status_code=404, detail="Alert not found")

    row = dict(zip(existing.column_names, existing.result_rows[0]))
    row["status"] = body.status.value
    row["version"] = row["version"] + 1

    await client.insert(
        "alerts",
        [list(row.values())],
        column_names=list(row.keys()),
    )

    return {"id": alert_id, "status": body.status.value}


@router.patch("/{alert_id}/assign")
async def assign_alert(alert_id: str, body: AlertAssign):
    
    client = await get_client()

    existing = await client.query(
        "SELECT * FROM alerts FINAL WHERE id = {id:String} LIMIT 1",
        parameters={"id": alert_id},
    )
    if not existing.result_rows:
        raise HTTPException(status_code=404, detail="Alert not found")

    row = dict(zip(existing.column_names, existing.result_rows[0]))
    row["assigned_analyst"] = body.assigned_analyst
    row["version"] = row["version"] + 1

    await client.insert(
        "alerts",
        [list(row.values())],
        column_names=list(row.keys()),
    )

    return {"id": alert_id, "assigned_analyst": body.assigned_analyst}