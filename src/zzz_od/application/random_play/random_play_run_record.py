from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord


class RandomPlayRunRecord(AppRunRecord):

    def __init__(self, instance_idx: Optional[int] = None, game_refresh_hour_offset: int = 0):
        AppRunRecord.__init__(
            self,
            'random_play',
            instance_idx=instance_idx,
            game_refresh_hour_offset=game_refresh_hour_offset
        )
