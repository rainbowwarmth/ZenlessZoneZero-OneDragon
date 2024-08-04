from typing import Optional

from one_dragon.base.operation.application_run_record import AppRunRecord


class ScratchCardRunRecord(AppRunRecord):

    def __init__(self, instance_idx: Optional[int] = None, game_refresh_hour_offset: int = 0):
        AppRunRecord.__init__(
            self,
            'scratch_card',
            instance_idx=instance_idx,
            game_refresh_hour_offset=game_refresh_hour_offset
        )
