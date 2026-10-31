import logging
import os

from vision_agents.core import User, Agent
from vision_agents.plugins import getstream, gemini

logger = logging.getLogger(__name__)


# --- 1. Agent Creation Function ---
async def create_agent_instance(user_id: str, user_name: str, instructions: str) -> Agent:
    """Initializes and returns the Agent instance with specific instructions."""
    llm = gemini.Realtime()

    agent = Agent(
        edge=getstream.Edge(
            api_key=os.getenv("STREAM_API_KEY"),
            api_secret=os.getenv("STREAM_API_SECRET"),
        ),
        agent_user=User(name=user_name, id=user_id),
        instructions=instructions,
        llm=llm,
    )
    return agent


# --- 2. Call Joining and Execution Function ---
async def start_call_agent(
    call_type: str, call_id: str, user_id: str, user_name: str, instructions: str
) -> None:
    """Creates agent, joins call, and runs the conversation loop."""
    try:
        logger.info("Creating agent for %s:%s", call_type, call_id)
        agent = await create_agent_instance(user_id, user_name, instructions)

        call = await agent.create_call(call_type, call_id)
        logger.info("Starting Gemini Realtime agent for %s:%s", call_type, call_id)

        async with agent.join(call):
            logger.info("Agent joined call %s", call_id)

            # simple_response is an async generator in this version:
            # iterate it, don't await it. Wrapped separately so a
            # greeting failure doesn't end the call.
            try:
                async for _ in agent.llm.simple_response(
                    "Hello there! I'm your AI assistant. How can I help you today?"
                ):
                    pass
            except Exception:
                logger.exception("Greeting failed in call %s (continuing)", call_id)

            # Keeps the connection open until the call ends
            await agent.finish()

    except Exception:
        logger.exception("Agent failed in call %s", call_id)
    finally:
        logger.info("Agent finished for call %s", call_id)
