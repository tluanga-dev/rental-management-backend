import logging
from celery import shared_task
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def test_task(self):
    """
    Test task to verify Celery is working properly.
    """
    logger.info("Test task executed successfully")
    return {
        'status': 'success',
        'timestamp': timezone.now().isoformat(),
        'message': 'Celery is working properly'
    }