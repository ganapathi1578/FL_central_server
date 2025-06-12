import asyncio
from channels.layers import get_channel_layer

# Frame → Future registry
pending_responses = {}

async def send_and_wait(house_id, frame, timeout=15):
    """
    Send 'frame' to the WebSocket group for house_id,
    wait for a matching response (frame.id) in pending_responses.
    """
    channel_layer = get_channel_layer()
    future = asyncio.get_event_loop().create_future()
    pending_responses[frame["id"]] = future

    await channel_layer.group_send(
        f"house_{house_id}",
        {"type": "forward.http", "frame": frame}
    )

    try:
        response = await asyncio.wait_for(future, timeout)
        return response
    finally:
        pending_responses.pop(frame["id"], None)
