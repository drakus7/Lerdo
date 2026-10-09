from fastapi import FastAPI
from app.routers import alerts, pipeline

app = FastAPI(title="SOC Dashboard API")

app.include_router(alerts.router)
app.include_router(pipeline.router)

@app.get("/")
async def root():
    return {"status":"ok","service":"soc-dashboard-api"}