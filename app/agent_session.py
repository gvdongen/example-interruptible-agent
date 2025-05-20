import restate
import logging
import random

from datetime import timedelta

from app.models import AgentResponse
from models import AgentInput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

agent_session = restate.VirtualObject("AgentSession")

NEW_INPUT_PROMISE = "new_input_promise"


@agent_session.handler()
async def run(ctx: restate.ObjectContext, req: AgentInput):
    input_items = req
    id, new_input_promise = ctx.awakeable(type_hint=AgentInput)
    ctx.set(NEW_INPUT_PROMISE, id)

    # run agent loop
    while True:
        agent_iteration = ctx.service_call(run_iteration_of_agent, arg=input_items)

        match await restate.select(new_input_promise=new_input_promise,
                                   agent_iteration=agent_iteration):
            case ['new_input_promise', new_input]:
                logger.info(f"Incorporating new input for {ctx.key()}: {new_input}")

                # cancel current iteration
                logger.info(f"Cancelling current iteration for {ctx.key()}")
                await agent_iteration.cancel_invocation()

                # set a new promise
                id, new_input_promise = ctx.awakeable()
                ctx.set(NEW_INPUT_PROMISE, id)

                # incorporate new input
                input_items = new_input

            case ['agent_iteration', output]:
                logger.info(f"Continuing: No new input for {ctx.key()}")
                input_items.message_history.append("Agent responded: " + output)
                if output == "Done":
                    logger.info(f"Agent run completed for {ctx.key()}")
                    break

    # send the result back to the caller
    from chat import process_agent_response
    ctx.object_send(
        process_agent_response,
        key=ctx.key(),
        arg=AgentResponse(
            final_output="This is the final output"
        ),
    )
    ctx.clear(NEW_INPUT_PROMISE)



@agent_session.handler(kind="shared")
async def incorporate_new_input(ctx: restate.ObjectSharedContext, req: AgentInput) -> bool:
    id = await ctx.get(NEW_INPUT_PROMISE)

    if id is None:
        logger.warning(f"No awakeable ID found. Maybe invocation finished in the meantime. Cannot incorporate new input for {ctx.key()}.")
        return False

    ctx.resolve_awakeable(id, req)
    logger.info(f"Resolved awakeable with ID {id} with new input for {ctx.key()}: {req}")
    return True


agent = restate.Service("Agent")

@agent.handler()
async def run_iteration_of_agent(ctx: restate.ObjectContext, input_items: AgentInput):
    # Randomly decide if the agent is done
    logger.info(f"Running iteration of agent for {ctx.key()} with input items: {input_items}")
    await ctx.sleep(timedelta(seconds=3))
    done = await ctx.run("llm call", lambda: random.randint(0, 100) < 10)
    if done:
        return "Done"
    else:
        return "Do another iteration"
