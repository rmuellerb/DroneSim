from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)

class SimulatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'simulator'

    def ready(self):
        import simulator.auth_hooks # noqa: F401
        logger.warning("SimulatorConfig.ready() loaded auth_hooks")
