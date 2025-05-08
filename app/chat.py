import restate

from models import ChatMessage, ChatHistory, AgentResponse, AgentInput

# Keyed by conversation ID
chat_service = restate.VirtualObject("ChatService")

# Keys of the K/V state stored in Restate per chat
CHAT_HISTORY = "chat_history"
ACTIVE_AGENT_INV_ID = "active_agent_inv_id"


@chat_service.handler()
async def process_user_message(ctx: restate.ObjectContext, req: ChatMessage):
    """
    Send a message from the customer to the ChatService.
    This will be used as input to start an agent session.

    Args:
        req (ChatMessage): The message to send to the ChatService.
    """

    history = await ctx.get(CHAT_HISTORY, type_hint=ChatHistory) or ChatHistory()
    history.entries.append(req)
    ctx.set(CHAT_HISTORY, history)

    ongoing_agent_run = await ctx.get(ACTIVE_AGENT_INV_ID)

    if ongoing_agent_run:
        # If there is an ongoing agent run, we need to cancel it
        ctx.cancel_invocation(ongoing_agent_run)

    # Reinvoke with the new message
    from agent_session import run as agent_session_run

    handle = ctx.object_send(
        agent_session_run,
        key=ctx.key(),
        arg=AgentInput(
            message_history=[
                entry.content for entry in history.entries
            ]  # this is the input for the LLM call
        ),
    )

    ctx.set(ACTIVE_AGENT_INV_ID, await handle.invocation_id())


@chat_service.handler()
async def process_agent_response(ctx: restate.ObjectContext, req: AgentResponse):
    """
    Receive an async response from the Agent.

    Args:
        req (ChatMessage): The message to send to add to the chat history.
    """

    new_message = ChatMessage(role="system", content=req.final_output)
    history = await ctx.get(CHAT_HISTORY, type_hint=ChatHistory) or ChatHistory()
    history.entries.append(new_message)
    ctx.set(CHAT_HISTORY, history)

    ctx.clear(ACTIVE_AGENT_INV_ID)
