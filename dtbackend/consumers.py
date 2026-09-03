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

class ParticipantConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.participant_id = self.scope['url_route']['kwargs']['participant_id']
        self.individual_group = f'participant_{self.participant_id}'
        # global Group for all Monitors
        self.global_group = 'all_participants'

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

    async def send_participant_message(self, event):
        # Wir holen das 'payload'-Objekt aus dem Event
        payload = event['payload']

        # Und senden es als JSON direkt ans Vue-Frontend
        await self.send(text_data=json.dumps(payload))

class ModeratorConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.individual_group = f'moderator'
        await self.channel_layer.group_add(self.individual_group, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Aus beiden Gruppen sauber austragen
        await self.channel_layer.group_discard(self.individual_group, self.channel_name)

    async def send_moderator_message(self, event):
        # Wir holen das 'payload'-Objekt aus dem Event
        payload = event['payload']

        # Und senden es als JSON direkt ans Vue-Frontend
        await self.send(text_data=json.dumps(payload))
        
class ParameterConsumer(AsyncWebsocketConsumer):
    GROUP = "parameters"

    # connect method is called when a WebSocket connection is established
    async def connect(self):
        await self.channel_layer.group_add(self.GROUP, self.channel_name)  # Add the client to the group
        await self.accept() # Accept the WebSocket connection

    # disconnect method is called when the WebSocket connection is closed
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.GROUP, self.channel_name) # Remove the client from the group

    # If the consumer receives a message from the WebSocket, it will send it to the group
    async def receive(self, text_data=None, bytes_data=None):
        content = json.loads(text_data)
        await self.channel_layer.group_send(
            self.GROUP,
            {
                "type": "parameter.change",
                "section": content["section"],
                "parameter": content["parameter"],
                "value": content["value"],
                "origin": self.channel_name,
            },
        )

    # This method is called when a message is sent to the group
    async def parameter_change(self, event):
        await self.send(text_data=json.dumps({
            "section": event["section"],
            "parameter": event["parameter"],
            "value": event["value"],
        }))
