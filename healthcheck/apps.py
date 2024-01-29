from django.apps import AppConfig

from health_check.plugins import plugin_dir


class MyAppConfig(AppConfig):
    name = "healthcheck"

    def ready(self):
        from .checks import (
            MailboxAuthenticationHealthCheck,
            LicencePayloadsHealthCheck,
            ManageInboxTaskHealthCheck,
            PendingMailHealthCheck,
        )

        plugin_dir.register(MailboxAuthenticationHealthCheck)
        plugin_dir.register(LicencePayloadsHealthCheck)
        plugin_dir.register(ManageInboxTaskHealthCheck)
        plugin_dir.register(PendingMailHealthCheck)