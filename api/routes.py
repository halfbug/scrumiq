from fastapi import APIRouter

from api.v1 import llm, usage, stream

api_router_v1 = APIRouter()

api_router_v1.include_router(llm.router, prefix="/llm", tags=["llm"])
api_router_v1.include_router(usage.router, prefix="/usage", tags=["usage"])
api_router_v1.include_router(stream.router, prefix="/chat", tags=["chat"])

# api_router.include_router(role.router, prefix="/role", tags=["role"])