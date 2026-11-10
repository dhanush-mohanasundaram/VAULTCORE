import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from sqlalchemy import text

from app.api import auth, products, cart, orders, admin
from app.config import settings
from app.database import engine

app = FastAPI(title="VAULTCORE — Secure Transaction-Safe E-Commerce API")

_cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_id_and_logging(request: Request, call_next: Callable):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    request.state.request_id = request_id
    start = time.time()

    try:
        response = await call_next(request)
    except Exception:
        latency = (time.time() - start) * 1000
        print(
            '{"level":"error","request_id":"%s","method":"%s","path":"%s","status":500,"latency_ms":%.2f,"error":"unhandled"}'
            % (request_id, request.method, request.url.path, latency)
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                }
            },
        )

    latency = (time.time() - start) * 1000
    print(
        '{"level":"info","request_id":"%s","method":"%s","path":"%s","status":%d,"latency_ms":%.2f}'
        % (request_id, request.method, request.url.path, response.status_code, latency)
    )
    response.headers["x-request-id"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"http_{exc.status_code}",
                "message": exc.detail if isinstance(exc.detail, str) else "Request failed",
                "request_id": request_id,
            }
        },
    )


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/health")
def health():
    """Health endpoint that verifies database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": "disconnected"},
        )
