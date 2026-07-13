import json
from channels.generic.websocket import AsyncWebsocketConsumer

class MonitorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.monitor_id = self.scope['url_route']['kwargs']['monitor_id']
        self.individual_group = f'monitor_{self.monitor_id}'
        # global Group for all Monitors
        self.global_group = 'all_monitors'

        await self.channel_layer.group_add(self.individual_group, self.channel_name)
        await self.channel_layer.group_add(self.global_group, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Aus beiden Gruppen sauber austragen
        await self.channel_layer.group_discard(self.individual_group, self.channel_name)
        await self.channel_layer.group_discard(self.global_group, self.channel_name)


    # Diese Methode wird aufgerufen, wenn eine Nachricht an die Gruppe gesendet wird
    #async def send_monitor_message(self, event):
    #    message = event['message']
#
#        # Nachricht als JSON an das Vue-Frontend senden
#        await self.send(text_data=json.dumps({
#            'message': message
#        }))

    async def send_monitor_message(self, event):
        # Wir holen das 'payload'-Objekt aus dem Event
        payload = event['payload']

        # Und senden es als JSON direkt ans Vue-Frontend
        await self.send(text_data=json.dumps(payload))
