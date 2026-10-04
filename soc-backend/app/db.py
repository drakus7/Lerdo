import os
import clickhouse_connect
from clickhouse_connect.driver.asyncclient import AsyncClient

CH_HOST = os.getenv("CH_HOST","localhost")
CH_PORT = int(os.getenv("CH_PORT","8123"))
CH_DATABASE = os.getenv("CH_DATABASE","soc_dashboard")

_client: AsyncClient | None = None

async def get_client() -> AsyncClient:
    global _client
    if _client is None:
        _client = await clickhouse_connect.get_async_client(host=CH_HOST,port=CH_PORT,database=CH_DATABASE)
        return _client