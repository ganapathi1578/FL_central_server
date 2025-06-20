import json, hashlib
from channels.generic.websocket import AsyncWebsocketConsumer
from django.utils import timezone
from .models import HouseTunnel
from .utils import pending_responses
from channels.db import database_sync_to_async


class TunnelConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("✅ WebSocket connected!") 
        await self.accept()
        self.house_id = None  # To keep track of which house_id is connected

    async def disconnect(self, close_code):
        if self.house_id:
            try:
                tunnel = await database_sync_to_async(HouseTunnel.objects.get)(house_id=self.house_id)
                tunnel.connected = False
                await database_sync_to_async(tunnel.save)()
                await self.channel_layer.group_discard(f"house_{self.house_id}", self.channel_name)
            except HouseTunnel.DoesNotExist:
                pass  # Safe fail

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get("action")

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

            tunnel.connected = True
            tunnel.last_seen = timezone.now()
            await database_sync_to_async(tunnel.save)()
            await self.channel_layer.group_add(f"house_{hid}", self.channel_name)
            self.house_id = hid  # track it for disconnect
            await self.send(json.dumps({"status": "ok"}))
            return

        if action == "http_response":
            frame_id = data.get("id")
            future = pending_responses.get(frame_id)
            if future:
                future.set_result(data)
            return
    async def forward_http(self, event):
        print("📤 Forwarding event to house:", event)
        await self.send(text_data=json.dumps(event))