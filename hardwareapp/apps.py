from django.apps import AppConfig


class HardwareappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hardwareapp'
    verbose_name = 'Hardware'

    def ready(self):
        import hardwareapp.signals  # noqa: F401
        import hardwareapp.machine_history_signals  # noqa: F401
