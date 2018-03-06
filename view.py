import math

from pyplanet.views.generics.widget import WidgetView
from pyplanet.views.template import TemplateView
from pyplanet.utils import times
import logging


class CheckCheckView(WidgetView):
    
    widget_x = 20
    widget_y = -70

    template_name = 'checkcheck/checkcheckwidget.xml'

    def __init__(self, app):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.id = 'pyplanet__widgets_checkcheck'
        self.subscribe('checkpointbla', self.handle_catch_all)

    async def get_player_data(self):
        data = await super().get_player_data()
        warnings = {}
        for idx, player in enumerate(self.app.instance.player_manager.online):
            if player.login in self.app.evidences:
                evidence = self.app.evidences[player.login]
                if evidence == None:
                    warnings[player.login] = {"message": ""}
                elif evidence < 0.34:
                    warnings[player.login] = {"message": "$f44You might have missed some checkpoints!"}
                elif evidence == 1:
                    warnings[player.login] = {"message": ""}
                else:
                    warnings[player.login] = {"message": ""}
            else:
                warnings[player.login] = {'message': ""}
        data.update(warnings)

        return data

class EventInjection(TemplateView):

    template_name = 'checkcheck/event_injection.xml'

    def __init__(self, app, callback):
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.id = 'pyplanet__views_checkcheck_event'
        self.callback = callback

    async def handle_catch_all(self, player, action, values, **kwargs):
        action_name = "checkpoint__"
        if(action.startswith(action_name)):
            data = action[len(action_name):].split("|")
            if len(data) == 2 and data[1].isdigit():
                await self.callback(player, data[0], int(data[1]))

