import logging

import zroya

from notification.notificator import Notificator


class WindowsToast(Notificator):
    def __init__(self):
        status = zroya.init("GitLFS Auto-Locker", "Your company", "git-lfs-auto-locker", "main", "v0.01")  # TODO: Company from config file
        if not status:
            logging.error("Zroya initialization failed")

        self._template_info = zroya.Template(zroya.TemplateType.Text1)
        self._template_info.setAudio(zroya.Audio.Default, mode=zroya.AudioMode.Silence)
        self._template_info.setExpiration(3600000)  # TODO: Buttons: Force unlock, show all locks

        self._template_warning = zroya.Template(zroya.TemplateType.ImageAndText4)

        self._template_error = zroya.Template(zroya.TemplateType.ImageAndText4)

    def show_info(self, message) -> None:
        self._template_info.setFirstLine(message)
        zroya.show(self._template_info)

    def show_warning(self, message) -> None:
        self._template_warning.setFirstLine(message)
        zroya.show(self._template_warning)

    def show_error(self, message) -> None:
        self._template_error.setFirstLine(message)
        zroya.show(self._template_error)
