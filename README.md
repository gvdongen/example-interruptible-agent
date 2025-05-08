# Restate AI Agents examples

A small example of an interruptible agent, that gets invoked via a chat session.

Important files:
- [`chat.py`](chat.py): The chat VO, which receives the user input and agent responses.
- [`agent_session.py`](agent_session.py): The agent session VO, which manages executes the agent loop.

To run Restate:
```shell
restate-server
```

Open the UI on http://localhost:9070 and register your deployment running at `http://localhost:9080`.

Then, start a task:
```shell
curl localhost:8080/ChatService/bob/process_user_message \
  -H 'idempotent-key: 12345' \
  --json '{
  "content": "do something",
  "role": "user"
}'
```

Then, start a new task and cancel the previous one:

```shell
curl localhost:8080/ChatService/bob/process_user_message \
  -H 'idempotent-key: 123456' \
  --json '{
  "content": "do something else",
  "role": "user"
}'
```

You can now see in the UI that the first task was canceled and the second one is running.

<img src="img.png" width="600px"/>