from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.tickets import router as tickets_router
from api.routes.health import router as health_router
from observability.error_tracking import init_sentry

init_sentry()

app = FastAPI(
    title="Support Router API",
    description="AI-powered customer support ticket routing and response system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets_router, tags=["tickets"])
app.include_router(health_router, tags=["health"])


@app.get("/")
async def root():
    return {
        "name": "Support Router API",
        "version": "1.0.0",
        "docs": "/docs"
    }