"""
LLM wrapper using Groq's hosted Llama API with OpenAI-style tool calling.

Maintains the full conversation history across turns so the model has
context of the entire session.
"""

import json
import logging
import re
from openai import OpenAI
from config import CEREBRAS_API_KEY, LLM_MODEL, SYSTEM_PROMPT
from tools import TOOL_SCHEMAS, TOOL_DISPATCH

logger = logging.getLogger(__name__)

_client = OpenAI(
    api_key=CEREBRAS_API_KEY,
    base_url="https://api.cerebras.ai/v1",
)

# Conversation history persists across turns.
_messages: list[dict] = [
    {"role": "system", "content": SYSTEM_PROMPT},
]


def reset_history() -> None:
    """Clear conversation history (keeps the system prompt)."""
    _messages.clear()
    _messages.append({"role": "system", "content": SYSTEM_PROMPT})


import re


def _coerce_arg_types(fn_name: str, args: dict) -> dict:
    """Best-effort coercion for args that arrive as strings but should be int/bool."""
    # Map of param names that must be integers.
    INT_PARAMS = {"days_ahead", "max_results"}
    BOOL_PARAMS = {"add_meet_link"}
    coerced = {}
    for k, v in args.items():
        if k in INT_PARAMS and isinstance(v, str):
            try:
                v = int(v)
            except ValueError:
                pass
        elif k in BOOL_PARAMS and isinstance(v, str):
            v = v.lower() in ("true", "1", "yes")
        coerced[k] = v
    return coerced


def _parse_failed_generation(err_str: str) -> list[tuple[str, dict]]:
    """Extract tool calls from Groq failed_generation string.

    Handles several malformed formats the model produces:
      <function=name({"key": "val"})</function>
      <function=name{"key": "val"}</function>
      <function=name [{"key": "val"}]</function>
      <function=name>()</function>   (no-arg call)
    """
    calls = []
    # [^{]* consumes anything between function name and opening brace,
    # including spaces, square brackets, or parentheses.
    pattern = r'<function=([a-zA-Z0-9_]+)[^{]*(\{.*?\})'
    for match in re.finditer(pattern, err_str, re.DOTALL):
        name, args_json = match.groups()
        try:
            args = json.loads(args_json)
            if isinstance(args, dict):
                calls.append((name, _coerce_arg_types(name, args)))
        except Exception:
            pass

    # Handle no-arg calls like <function=get_current_time>()</function>
    if not calls:
        no_arg_pattern = r'<function=([a-zA-Z0-9_]+)>\s*\(\s*\)'
        for match in re.finditer(no_arg_pattern, err_str):
            calls.append((match.group(1), {}))

    return calls


def chat(user_text: str, messages: list = None) -> str:
    """Send the user's message to the LLM and return the assistant's reply.

    Handles tool calls automatically: if the model requests a tool call,
    the tool is executed locally and the result is fed back so the model
    can produce a final natural-language answer.
    """
    if messages is None:
        messages = _messages

    messages.append({"role": "user", "content": user_text})

    try:
        response = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
        )
    except Exception as e:
        err_str = str(e)
        recovered_calls = _parse_failed_generation(err_str)
        if recovered_calls:
            logger.info("  [LLM recovery] Recovered tool call from model generation output.")
            # Execute recovered tool calls.
            for fn_name, fn_args in recovered_calls:
                logger.info(f"  [Tool call] {fn_name}({fn_args})")
                fn = TOOL_DISPATCH.get(fn_name)
                result = fn(**fn_args) if fn else json.dumps({"error": f"Unknown tool: {fn_name}"})
                messages.append({
                    "role": "system",
                    "content": f"Tool result for {fn_name}: {result}",
                })
            # Call model again to generate final natural response.
            try:
                second_resp = _client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=messages,
                )
                reply = second_resp.choices[0].message.content or ""
                messages.append({"role": "assistant", "content": reply})
                return reply
            except Exception as second_e:
                logger.error(f"  [LLM error] {second_e}")
                return f"Sorry, I had trouble completing the response. Error: {second_e}"

        error_msg = f"Sorry, I had trouble thinking about that. Error: {e}"
        logger.error(f"  [LLM error] {e}")
        messages.append({"role": "assistant", "content": error_msg})
        return error_msg

    message = response.choices[0].message

    # --- Handle tool calls (possibly chained) --------------------------
    # The model may request one or more tool calls before giving a final
    # text reply.  We loop until the model responds with plain content.
    while message.tool_calls:
        # Append the assistant message that contains the tool call(s).
        msg_dict = {
            "role": "assistant",
            "content": message.content or None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in message.tool_calls
            ],
        }
        messages.append(msg_dict)

        for tool_call in message.tool_calls:
            fn_name = tool_call.function.name
            args = {}
            if tool_call.function.arguments:
                try:
                    parsed = json.loads(tool_call.function.arguments)
                    if isinstance(parsed, dict):
                        args = parsed
                except json.JSONDecodeError:
                    pass
            
            logger.info(f"  [Tool call] {fn_name}({args})")

            # Execute the tool.
            fn = TOOL_DISPATCH.get(fn_name)
            if fn:
                result = fn(**args)
            else:
                result = json.dumps({"error": f"Unknown tool: {fn_name}"})

            # Feed the result back to the model.
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result,
            })

        # Ask the model to continue with the tool results.
        try:
            response = _client.chat.completions.create(
                model=LLM_MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
            )
        except Exception as e:
            error_msg = f"Sorry, something went wrong after the tool call. Error: {e}"
            logger.error(f"  [LLM error] {e}")
            return error_msg

        message = response.choices[0].message

    # Final text reply.
    reply = message.content or ""
    messages.append({"role": "assistant", "content": reply})
    return reply


def stream_chat(user_text: str, messages: list = None):
    """Yields text chunks as they are generated by the LLM.
    
    If the LLM decides to call a tool, it aggregates the stream, executes
    the tool, and recursively calls itself to stream the final response.
    """
    if messages is None:
        messages = _messages

    if user_text:
        messages.append({"role": "user", "content": user_text})

    try:
        response_stream = _client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            stream=True,
        )
    except Exception as e:
        yield f"Sorry, I had trouble thinking about that. Error: {e}"
        return

    # Track states
    is_tool_call = False
    tool_calls_agg = {}  # index -> {id, name, arguments}
    full_text = ""

    for chunk in response_stream:
        delta = chunk.choices[0].delta if chunk.choices else None
        if not delta:
            continue

        if delta.tool_calls:
            is_tool_call = True
            for tc_chunk in delta.tool_calls:
                idx = tc_chunk.index
                if idx not in tool_calls_agg:
                    tool_calls_agg[idx] = {"id": tc_chunk.id, "name": tc_chunk.function.name, "arguments": ""}
                if tc_chunk.function.arguments:
                    tool_calls_agg[idx]["arguments"] += tc_chunk.function.arguments
        elif not is_tool_call and delta.content:
            full_text += delta.content
            yield delta.content

    if not is_tool_call:
        messages.append({"role": "assistant", "content": full_text})
        return

    # --- We had tool calls ---
    tool_calls_list = []
    for idx, tc in sorted(tool_calls_agg.items()):
        tool_calls_list.append({
            "id": tc["id"],
            "type": "function",
            "function": {
                "name": tc["name"],
                "arguments": tc["arguments"],
            }
        })

    messages.append({
        "role": "assistant",
        "content": None,
        "tool_calls": tool_calls_list,
    })

    # Execute tools
    for tc in tool_calls_list:
        fn_name = tc["function"]["name"]
        try:
            fn_args = json.loads(tc["function"]["arguments"] or "{}")
        except Exception:
            fn_args = {}
            
        logger.info(f"  [Tool call] {fn_name}({fn_args})")
        fn = TOOL_DISPATCH.get(fn_name)
        if fn:
            result = fn(**fn_args)
        else:
            result = json.dumps({"error": f"Unknown tool: {fn_name}"})

        messages.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": result,
        })

    # Recurse to generate the text response now that tools are executed.
    # Pass empty user_text so it doesn't append a new user message.
    yield from stream_chat("", messages=messages)
