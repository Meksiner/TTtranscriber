# app_module.py
from litestar import Litestar, get

@get("/")
async def index() -> dict:
    return {"status": "ok", "message": "Granian + Litestar работает!"}

app = Litestar(route_handlers=[index], openapi_config=None)
