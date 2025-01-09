from fastapi import APIRouter, Request
from sse_starlette.sse import EventSourceResponse
from typing import AsyncGenerator
import asyncio

router = APIRouter()

@router.get("/sse/clone-progress/{task_id}")
async def clone_progress(request: Request, task_id: str) -> EventSourceResponse:
    async def event_generator() -> AsyncGenerator[dict, None]:
        while True:
            if await request.is_disconnected():
                break
                
            # 从内存中获取任务进度
            progress = request.app.state.tasks.get(task_id)
            if progress:
                yield {
                    "event": "progress",
                    "data": progress.json()
                }
                
            await asyncio.sleep(0.5)
            
    return EventSourceResponse(event_generator())
