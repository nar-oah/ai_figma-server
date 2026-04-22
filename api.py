from fastapi import APIRouter
from models import GenReq, GenRes, HealthRes
from service import get_gen_res

router = APIRouter()


@router.get("/healthz", response_model=HealthRes)
def get_health() -> HealthRes:
    return HealthRes(status="ok")


@router.post("/api/generate", response_model=GenRes)
def add_gen(req: GenReq) -> GenRes:
    return get_gen_res(req)
