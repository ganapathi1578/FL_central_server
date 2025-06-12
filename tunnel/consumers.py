import json, hashlib
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from .models import HouseTunnel
from .utils import pending_responses
from channels.db import database_sync_to_async



class TunnelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

        # 1) Registration / Authentication
        if action == "authenticate":
            hid = data.get("house_id")
            auth_hash = data.get("auth_hash")
            try:
                tunnel = await database_sync_to_async(HouseTunnel.objects.get)(house_id=hid)
            except HouseTunnel.DoesNotExist:
                return await self.close()

            expected = hashlib.sha256((hid + tunnel.secret_key).encode()).hexdigest()
            if auth_hash != expected:
                return await self.close()

            # Mark connected and join group
            tunnel.connected = True
            tunnel.last_seen = timezone.now()
            await database_sync_to_async(tunnel.save)()
            await self.channel_layer.group_add(f"house_{hid}", self.channel_name)
            await self.send(json.dumps({"status":"ok"}))
            return

        # 2) Response from home agent back to proxy
        if action == "http_response":
            frame_id = data.get("id")
            future = pending_responses.get(frame_id)
            if future:
                future.set_result(data)
            return

    async def forward_http(self, event):
        # Event from proxy; forward to home agent
        frame = event["frame"]
        await self.send(text_data=json.dumps(frame))
