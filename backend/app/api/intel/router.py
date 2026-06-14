# -*- coding: utf-8 -*-
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
async def intel_status():
    return {"module": "intelligence", "status": "operational", "source": "Global-Intelligence"}


@router.get("/reports")
async def list_intel_reports():
    return {"reports": [], "total": 0}


@router.get("/feeds")
async def list_intel_feeds():
    return {"feeds": [], "total": 0}
