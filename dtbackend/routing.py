from django.urls import re_path
from dtbackend import consumers

websocket_urlpatterns = [
    # match: ws://localhost:8000/ws/monitor/<id>/
    re_path(r'^ws/monitor/(?P<monitor_id>\d+)/$', consumers.MonitorConsumer.as_asgi()),
    re_path(r'^ws/participant/(?P<participant_id>\d+)/$', consumers.ParticipantConsumer.as_asgi()),
    re_path(r"ws/parameters/$", consumers.ParameterConsumer.as_asgi())
]
