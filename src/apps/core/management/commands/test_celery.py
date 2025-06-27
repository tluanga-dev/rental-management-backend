from django.core.management.base import BaseCommand
from core.tasks import check_item_count, get_current_item_count, check_low_stock_items
from celery import current_app
import json


class Command(BaseCommand):
    help = 'Test Celery tasks and check system item counts'

    def add_arguments(self, parser):
        parser.add_argument(
            '--task',
            type=str,
            choices=['count', 'low-stock', 'status'],
            default='count',
            help='Which task to run: count (item count), low-stock (low stock check), or status (celery status)'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run task asynchronously (requires celery worker)',
        )

    def handle(self, *args, **options):
        task_type = options['task']
        run_async = options['async']

        self.stdout.write(
            self.style.SUCCESS(f'Running Celery task: {task_type}')
        )

        try:
            if task_type == 'status':
                self.check_celery_status()
            elif task_type == 'count':
                self.run_item_count_task(run_async)
            elif task_type == 'low-stock':
                self.run_low_stock_task(run_async)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error running task: {e}')
            )

    def check_celery_status(self):
        """Check Celery configuration and status"""
        app = current_app
        
        self.stdout.write("=== Celery Configuration ===")
        self.stdout.write(f"Broker URL: {app.conf.broker_url}")
        self.stdout.write(f"Result Backend: {app.conf.result_backend}")
        self.stdout.write(f"Timezone: {app.conf.timezone}")
        
        # Check if beat schedule is configured
        beat_schedule = app.conf.beat_schedule
        if beat_schedule:
            self.stdout.write("\n=== Scheduled Tasks ===")
            for task_name, config in beat_schedule.items():
                self.stdout.write(f"Task: {task_name}")
                self.stdout.write(f"  Schedule: {config.get('schedule')} seconds")
                self.stdout.write(f"  Task: {config.get('task')}")
        
        # Try to inspect active workers (this will only work if workers are running)
        try:
            inspect = app.control.inspect()
            active_queues = inspect.active_queues()
            if active_queues:
                self.stdout.write("\n=== Active Workers ===")
                for worker, queues in active_queues.items():
                    self.stdout.write(f"Worker: {worker}")
                    for queue in queues:
                        self.stdout.write(f"  Queue: {queue['name']}")
            else:
                self.stdout.write(
                    self.style.WARNING("\nNo active workers found. This is normal for Railway deployment.")
                )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"\nCannot inspect workers: {e}")
            )

    def run_item_count_task(self, run_async):
        """Run the item count task"""
        if run_async:
            # Run asynchronously (requires celery worker)
            result = get_current_item_count.delay()
            self.stdout.write(f"Task submitted with ID: {result.id}")
            self.stdout.write("Check celery worker logs for results")
        else:
            # Run synchronously
            result = get_current_item_count()
            self.stdout.write("\n=== Item Count Results ===")
            self.stdout.write(json.dumps(result, indent=2))

    def run_low_stock_task(self, run_async):
        """Run the low stock check task"""
        if run_async:
            # Run asynchronously (requires celery worker)
            result = check_low_stock_items.delay()
            self.stdout.write(f"Task submitted with ID: {result.id}")
            self.stdout.write("Check celery worker logs for results")
        else:
            # Run synchronously
            result = check_low_stock_items()
            self.stdout.write("\n=== Low Stock Check Results ===")
            self.stdout.write(json.dumps(result, indent=2))
