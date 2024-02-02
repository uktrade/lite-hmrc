from django.apps import AppConfig
from django.db.models.signals import post_migrate


class MockHmrcConfig(AppConfig):
    name = "mock_hmrc"

    @classmethod
    def initialize_send_licence_usage_figures_to_lite_api(cls, **kwargs):
        pass

    def ready(self):
        post_migrate.connect(self.initialize_send_licence_usage_figures_to_lite_api, sender=self)
