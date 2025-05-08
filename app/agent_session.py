import asyncio

import restate

from chat import process_agent_response
from models import AgentInput, AgentResponse

agent_session = restate.VirtualObject("AgentSession")


@agent_session.handler()
async def run(ctx: restate.ObjectContext, req: AgentInput):

    # run agent loop
    async def run_agent_session() -> str:
        # Implement the logic for running the agent session here
        await asyncio.sleep(60)
        return "Agent says hello"

    output = await ctx.run("run agent session", run_agent_session)

    ctx.object_send(
        process_agent_response, key=ctx.key(), arg=AgentResponse(final_output=output)
    )
