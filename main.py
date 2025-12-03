import os
import uvicorn
import asyncio
from fastapi import FastAPI, HTTPException

from pydantic import BaseModel
from dotenv import load_dotenv

# Import the core logic from your new file
from agent_service import start_call_agent 

# --- 1. Initialization ---
load_dotenv() # Load env variables here
app = FastAPI()

# Pydantic model for the JSON payload from Next.js
class CallTrigger(BaseModel):
    call_id: str
    call_type: str = "default" # Use a default if your Next.js doesn't provide it
    instructions: str
    agent_user_id: str # Keep this
    agent_user_name: str # 💡 NEW FIELD ADDED
    # Note: The agent_user_id is now hardcoded inside create_agent_instance for simplicity


# Dictionary to track running tasks (optional, but good for cleanup/status)
active_tasks = {}


# --- 2. The Trigger Endpoint ---
@app.post("/api/join-call")
async def join_call_endpoint(trigger: CallTrigger):
    """Receives the trigger from Next.js and starts the agent in the background."""
    call_cid = f"{trigger.call_type}:{trigger.call_id}"

    if call_cid in active_tasks:
        return {"status": "warning", "message": "Agent already active."}

    # Start the agent connection loop asynchronously using asyncio.create_task
    task = asyncio.create_task(
        start_call_agent(trigger.call_type, trigger.call_id, trigger.agent_user_id,trigger.agent_user_name, trigger.instructions)

        # call_type: str, call_id: str, user_id: str, user_name: str, instructions: str
    )
    active_tasks[call_cid] = task
    
    # Immediately return success to Next.js/Stream webhook
    return {"status": "ok", "message": f"Agent joining call {trigger.call_id} in the background."}


# --- 3. Run Server ---
if __name__ == "__main__":
    if not all([os.getenv("STREAM_API_KEY"), os.getenv("STREAM_API_SECRET"), os.getenv("GOOGLE_API_KEY")]):
        print("FATAL: Please set all required environment variables.")
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)