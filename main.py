import os
import asyncio
import logging

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

# Logging must be configured before anything else logs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from agent_service import start_call_agent  # noqa: E402

REQUIRED_ENV = ("STREAM_API_KEY", "STREAM_API_SECRET", "GOOGLE_API_KEY")
missing = [k for k in REQUIRED_ENV if not os.getenv(k)]
if missing:
    logger.error("Missing environment variables: %s", missing)

app = FastAPI()

# Keeps track of running agents so the same call isn't joined twice
active_tasks: dict[str, asyncio.Task] = {}


# --- 1. Request model ---
class CallTrigger(BaseModel):
    call_type: str
    call_id: str
    agent_user_id: str
    agent_user_name: str
    instructions: str


def _on_done(call_cid: str):
    """Runs when an agent task ends: frees the slot and logs any crash."""
    def _cb(task: asyncio.Task):
        active_tasks.pop(call_cid, None)  # allows joining the same call again
        if task.cancelled():
            logger.info("Agent task %s was cancelled", call_cid)
        elif task.exception():
            logger.error("Agent task %s crashed", call_cid, exc_info=task.exception())
    return _cb


# --- 2. The Trigger Endpoint ---
@app.post("/api/join-call")
async def join_call_endpoint(trigger: CallTrigger):
    """Receives the trigger from Next.js and starts the agent in the background."""
    call_cid = f"{trigger.call_type}:{trigger.call_id}"
    logger.info("join-call received: %s (agent user: %s)", call_cid, trigger.agent_user_id)

    if call_cid in active_tasks:
        logger.warning("Agent already active for %s", call_cid)
        return {"status": "warning", "message": "Agent already active."}

    task = asyncio.create_task(
        start_call_agent(
            trigger.call_type,
            trigger.call_id,
            trigger.agent_user_id,
            trigger.agent_user_name,
            trigger.instructions,
        )
    )
    task.add_done_callback(_on_done(call_cid))
    active_tasks[call_cid] = task

    return {"status": "ok", "message": f"Agent joining call {trigger.call_id} in the background."}


@app.get("/health")
async def health():
    return {"status": "ok", "active_calls": list(active_tasks.keys())}


# --- 3. Run Server (only used with `python main.py`) ---
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)