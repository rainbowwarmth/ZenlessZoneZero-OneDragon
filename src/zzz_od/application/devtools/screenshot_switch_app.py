import time

from one_dragon.base.operation.context_base import ContextKeyboardEventEnum
from one_dragon.base.operation.operation import OperationRoundResult, OperationNode
from one_dragon.utils import debug_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.application.zzz_application import ZApplication
from zzz_od.context.zzz_context import ZContext


class ScreenshotSwitchApp(ZApplication):

    def __init__(self, ctx: ZContext):
        """
        按闪避的时候自动截图 用于保存素材训练模型
        """
        ZApplication.__init__(
            self,
            ctx=ctx,
            op_name=gt('闪避截图', 'ui')
        )

        self.to_save_screenshot: bool = False  # 去保存截图 由按键触发
        self.last_save_screenshot_time: float = 0  # 上次保存截图时间

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        screenshot = OperationNode('持续截图', self.repeat_screenshot)
        save = OperationNode('保存截图', self.do_save_screenshot)
        self.add_edge(screenshot, save)
        self.add_edge(save, screenshot)

        self.param_start_node = screenshot

    def handle_init(self) -> None:
        """
        执行前的初始化 由子类实现
        注意初始化要全面 方便一个指令重复使用
        """
        self.ctx.controller.max_screenshot_cnt = 10  # 需要保留多一点的图片
        self.ctx.listen_event(ContextKeyboardEventEnum.PRESS.value, self._on_key_press)

    def repeat_screenshot(self) -> OperationRoundResult:
        """
        持续截图
        """
        self.screenshot()
        if self.to_save_screenshot:
            return self.round_success()
        else:
            return self.round_wait(wait_round_time=0.02)

    def _on_key_press(self, key: str) -> None:
        """
        按键监听
        """
        if self.to_save_screenshot:  # 上轮截图还没有完成保存
            return
        if time.time() - self.last_save_screenshot_time <= 1:  # 每秒最多保持一次 防止战斗中按得太多
            return
        if key not in [
            self.ctx.game_config.key_change_next,
            self.ctx.game_config.key_change_prev
        ]:
            return

        self.to_save_screenshot = True

    def do_save_screenshot(self) -> OperationRoundResult:
        """
        保存截图
        """
        screen_history = self.ctx.controller.screenshot_history.copy()
        for screen in screen_history:
            debug_utils.save_debug_image(screen.image, prefix='switch')

        self.to_save_screenshot = False
        self.last_save_screenshot_time = time.time()

        return self.round_success()
