from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.database import init_db
from core.errors import register_exception_handlers
from core.settings import get_settings
from modules.mrp.router import router as mrp_router
from modules.products.router import router as products_router
from modules.work_orders.router import router as work_orders_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(products_router)
    app.include_router(work_orders_router)
    app.include_router(mrp_router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()


@app.on_event("startup")
def on_startup():
    init_db()


