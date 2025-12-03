import logging
import os
import asyncio
from vision_agents.core import User, Agent
from vision_agents.plugins import getstream, gemini

logger = logging.getLogger(__name__)

# --- 1. Agent Creation Function ---
async def create_agent_instance( user_id: str, user_name: str, instructions: str) -> Agent:
    """Initializes and returns the Agent instance with specific instructions."""
    
    # 1.1 Initialize Gemini with realtime capabilities
    llm = gemini.Realtime()

    # 1.2 Create the Agent
    agent = Agent(
        edge=getstream.Edge(
            api_key=os.getenv("STREAM_API_KEY"),
            api_secret=os.getenv("STREAM_API_SECRET")
        ),
        agent_user=User(name=user_name, id=user_id), # Use a fixed, unique ID
        instructions=instructions,
        llm=llm,
    )
    return agent

# --- 2. Call Joining and Execution Function ---
# --- 2. Call Joining and Execution Function ---
async def start_call_agent(call_type: str, call_id: str, user_id: str, user_name: str, instructions: str) -> None:
    """Creates agent, joins call, and runs the conversation loop."""
    
    agent = await create_agent_instance(user_id, user_name, instructions)

    # Note: Use the call_id as the room ID
    call = await agent.create_call(call_type, call_id)

    logger.info(f"🤖 Starting Gemini Realtime Agent for {call_type}:{call_id}...")

    try:
        # 🟢 THE FIX IS HERE: Await the agent.join(call) method itself
        async with await agent.join(call):
            logger.info(f"Agent joined call {call_id}.")

            # Send initial message (agent speaks this)
            await agent.llm.simple_response("Hello there! I'm your AI assistant. How can I help you today?")
            
            # Run till the call ends (maintains the connection and listens for user input)
            await agent.finish()
            
    except Exception as e:
        logger.error(f"Agent failed in call {call_id}: {e}")
    finally:
        logger.info(f"Agent finished for call {call_id}.")