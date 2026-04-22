from __future__ import annotations
from fastapi import APIRouter
from app.models import GenReq, GenRes, HealthRes
from app.service import get_gen_res

router = APIRouter()


@router.get("/healthz", response_model=HealthRes)
def get_health() -> HealthRes:
    return HealthRes(status="ok")


@router.post("/api/generate", response_model=GenRes)
def add_gen(req: GenReq) -> GenRes:
    return get_gen_res(req)
