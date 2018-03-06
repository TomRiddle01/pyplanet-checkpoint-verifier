from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.trackmania import callbacks as tm_signals
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals

from pyplanet.apps.core.maniaplanet.callbacks.player import player_chat

from pyplanet.apps.core.maniaplanet.models import Player

import asyncio

from .view import CheckCheckView
from .view import EventInjection
from .models import CheckpointOrder


class CheckcheckApp(AppConfig):
    game_dependencies = ['trackmania', 'shootmania']
    mode_dependencies = ['TimeAttack']
    app_dependencies = ['core.maniaplanet']
    


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


    async def on_init(self):
        await super().on_init()

    async def on_stop(self):
        await super().on_stop()

    async def on_destroy(self):
        await super().on_destroy()

    async def on_start(self):
        await super().on_start()

        tm_signals.finish.register(self.on_finish)
        tm_signals.give_up.register(self.on_give_up)
        tm_signals.start_countdown.register(self.on_start_countdown)
        mp_signals.map.map_begin.register(self.on_map_begin)

        await self.init_variables()

        self.widget = CheckCheckView(self)
        self.widget.subscribe('details', self.on_details)
        self.event_injection = EventInjection(self, self.on_checkcheck_checkpoint)

        await self.widget.display()
        await self.event_injection.display()

    async def init_variables(self):
        self.current_paths = {}
        self.evidences = {}
        self.finished_paths = {}

        path_database = await CheckpointOrder.objects.execute(
            CheckpointOrder.select(CheckpointOrder, Player)
                .join(Player)
                .where(CheckpointOrder.map_id == self.instance.map_manager.current_map.get_id())
        )
        map_checkpoints = self.instance.map_manager.current_map.num_checkpoints

        for entry in list(path_database):
            cps = entry.checkpoints.split("|")
            if map_checkpoints == len(cps):
                self.finished_paths[entry.player.login] = cps


    async def on_details(self, player, *args, **kwargs):
        if not player.login in self.current_paths:
            self.current_paths[player.login] = []

        finished = len(self.finished_paths)
        current = self.current_paths[player.login]
        
        if len(current) == 0:
            await self.instance.chat("100% of {} recorded run(s) on this map match you at checkpoint {}.".format(finished, len(self.current_paths[player.login])), player)
        else:
            evidence = self.waypoint_probability(len(current)-1, current[-1])
            if evidence is not None:
                await self.instance.chat("{}% of {} recorded run(s) on this map match you at checkpoint {}.".format(int(evidence*100), finished, len(self.current_paths[player.login])), player)


    def waypoint_probability(self, waypoint_number, waypoint_id):
        same = 0
        paths = self.finished_paths
        if len(paths) == 0: return 1

        for user, path in paths.items():
            if waypoint_number < len(path) and path[waypoint_number] == waypoint_id:
                same += 1

        return same/len(paths)


    async def on_map_begin(self, **kwargs):
        await self.init_variables()
        await self.event_injection.display()


    async def on_checkcheck_checkpoint(self, player, checkpoint_position, checkpoint_number):
        if not player.login in self.current_paths:
            self.current_paths[player.login] = []

        self.current_paths[player.login].append(checkpoint_position)

        if(checkpoint_number+1 != len(self.current_paths[player.login])): 
            self.evidences[player.login] = None
            return


        evidence = self.waypoint_probability(len(self.current_paths[player.login])-1, checkpoint_position)
        self.evidences[player.login] = evidence

        # update own list
        await self.widget.display()


    async def on_start_countdown(self, time, player, flow):
        self.current_paths[player.login] = []
        self.evidences[player.login] = 1
        await self.widget.display(player=player.login)
        await self.event_injection.display(player=player.login)

    async def on_give_up(self, time, player, flow):
        self.current_paths[player.login] = []
        self.evidences[player.login] = 1
        await self.widget.display(player=player.login)
        await self.event_injection.display(player=player.login)

    async def on_finish(self, player, race_time, lap_time, cps, flow, raw, **kwargs):
        if not player.login in self.current_paths:
            self.current_paths[player.login] = []

        if len(cps) == len(self.current_paths[player.login]):
            self.finished_paths[player.login] = self.current_paths[player.login]

            checkpoint_order, created = await CheckpointOrder.get_or_create(
                map=self.instance.map_manager.current_map.get_id(), 
                player=player.get_id())
            checkpoint_order.checkpoints = "|".join(self.current_paths[player.login])
            await checkpoint_order.save()

        self.current_paths[str(player.login)] = []
        self.evidences[player.login] = 1
        await self.widget.display()

    async def on_chat(self, player, text, cmd, **kwargs):

        pass


