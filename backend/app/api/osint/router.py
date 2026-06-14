# -*- coding: utf-8 -*-
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def osint_status():
    return {"module": "osint", "status": "operational", "source": "Atalaya"}


@router.get("/cases")
async def list_cases():
    return {"cases": [], "total": 0}


@router.get("/entities")
async def list_entities():
    return {"entities": [], "total": 0}


@router.get("/jobs")
async def list_jobs():
    return {"jobs": [], "total": 0}


@router.get("/reports")
async def list_reports():
    return {"reports": [], "total": 0}


@router.get("/health")
async def osint_health():
    return {"status": "ok", "module": "osint"}


api_router = router
