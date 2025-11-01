from fastapi import FastAPI, Depends, Query
from sqlmodel import Session, select
from database import get_session, init_db
from routers.reports import router as reports_router
from datetime import date

app = FastAPI()

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/health")
def health(): return {"ok": True}

# Monta el router de reportes 
app.include_router(reports_router)