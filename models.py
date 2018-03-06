"""
checkcheck Models.
"""
from peewee import *
from pyplanet.core.db import TimedModel
from pyplanet.apps.core.maniaplanet.models import Map, Player


class CheckpointOrder(TimedModel):
    map = ForeignKeyField(Map, index=True)

    player = ForeignKeyField(Player, index=True)

    checkpoints = TextField(
        null=False, default=''
    )

    class Meta:
        indexes = (
            (('player', 'map'), True),
        )
