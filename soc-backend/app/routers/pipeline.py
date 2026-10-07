from fastapi import APIRouter
from app.db import get_client

router = APIRouter(prefix="/pipeline", tags=["pipeline"])

@router.get("/health")
async def pipeline_health():
    client = await get_client()

    result = await client.query(
        """
        SELECT snapshot_time, events_per_sec, log_seconds, error_count, buffer_size
        FROM pipeline_health
        ORDER BY snapshot_time DESC
        LIMIT 1
        """
    )

    if not result.result_rows:
        return {"status":"no_data", "message":"No pipeline_health snapshots yet"}

    row = dict(zip(result.column_names, result.result_rows[0]))

    if row["lag_seconds"] > 30 or row["error_count"] > 0:
        row["status"]="degraded"
    else:
        row["status"]="healthy"

    return row