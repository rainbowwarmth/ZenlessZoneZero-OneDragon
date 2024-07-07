from PySide6.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ProgressBar, IndeterminateProgressBar, SettingCardGroup, \
    FluentIcon

from one_dragon.envs.env_config import EnvConfig, env_config
from one_dragon.envs.project_config import ProjectConfig, project_config
from one_dragon.gui.component.interface.vertical_scroll_interface import VerticalScrollInterface
from one_dragon.gui.component.log_display_card import LogDisplayCard
from one_dragon.gui.install_card.all_install_card import AllInstallCard
from one_dragon.gui.install_card.code_install_card import CodeInstallCard
from one_dragon.gui.install_card.git_install_card import GitInstallCard
from one_dragon.gui.install_card.pip_install_card import PipInstallCard
from one_dragon.gui.install_card.python_install_card import PythonInstallCard
from one_dragon.gui.install_card.venv_install_card import VenvInstallCard
from one_dragon.utils.i18_utils import gt


class InstallerInterface(VerticalScrollInterface):

    def __init__(self, parent=None):
        content_widget = QWidget()
        v_layout = QVBoxLayout(content_widget)

        self.progress_bar = ProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setVisible(False)
        v_layout.addWidget(self.progress_bar)

        self.progress_bar_2 = IndeterminateProgressBar()
        self.progress_bar_2.setVisible(False)
        v_layout.addWidget(self.progress_bar_2)

        self.git_opt = GitInstallCard()
        self.git_opt.progress_changed.connect(self.update_progress)

        self.code_opt = CodeInstallCard()
        self.code_opt.progress_changed.connect(self.update_progress)

        self.python_opt = PythonInstallCard()
        self.python_opt.progress_changed.connect(self.update_progress)

        self.pip_opt = PipInstallCard()
        self.pip_opt.progress_changed.connect(self.update_progress)

        self.venv_opt = VenvInstallCard()
        self.venv_opt.progress_changed.connect(self.update_progress)

        self.all_opt = AllInstallCard([self.git_opt, self.code_opt, self.python_opt, self.pip_opt, self.venv_opt])

        update_group = SettingCardGroup(gt('运行环境', 'ui'))
        update_group.addSettingCard(self.all_opt)
        update_group.addSettingCard(self.git_opt)
        update_group.addSettingCard(self.code_opt)
        update_group.addSettingCard(self.python_opt)
        update_group.addSettingCard(self.pip_opt)
        update_group.addSettingCard(self.venv_opt)

        v_layout.addWidget(update_group)

        log_group = SettingCardGroup(gt('安装日志', 'ui'))
        self.log_card = LogDisplayCard(max_height=200)
        log_group.addSettingCard(self.log_card)
        v_layout.addWidget(log_group)

        VerticalScrollInterface.__init__(self, object_name='install_interface',
                                         parent=parent, content_widget=content_widget,
                                         nav_text_cn='一键安装', nav_icon=FluentIcon.CLOUD_DOWNLOAD)

        self.env_config: EnvConfig = env_config
        self.project_config: ProjectConfig = project_config

    def init_on_shown(self) -> None:
        """
        页面加载完成后 检测各个组件状态并更新显示
        :return:
        """
        self.git_opt.check_and_update_display()
        self.code_opt.check_and_update_display()
        self.python_opt.check_and_update_display()
        self.pip_opt.check_and_update_display()
        self.venv_opt.check_and_update_display()
        self.log_card.update_on_log = True

    def on_hidden(self) -> None:
        """
        子界面隐藏时的回调
        :return:
        """
        self.log_card.update_on_log = False

    def update_progress(self, progress: float, message: str) -> None:
        """
        进度回调更新
        :param progress: 进度 0~1
        :param message: 当前信息
        :return:
        """
        if progress == -1:
            self.progress_bar.setVisible(False)
            self.progress_bar_2.setVisible(True)
            self.progress_bar_2.start()
        else:
            self.progress_bar.setVisible(True)
            self.progress_bar.setVal(progress)
            self.progress_bar_2.setVisible(False)
            self.progress_bar_2.stop()
