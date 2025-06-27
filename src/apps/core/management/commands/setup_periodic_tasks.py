"""
Management command to set up periodic tasks in the database for django-celery-beat.
This is needed for Railway deployment where we use database-backed scheduling.
"""
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
import json


class Command(BaseCommand):
    help = 'Set up periodic tasks for Celery Beat in the database'

    def handle(self, *args, **options):
        self.stdout.write('Setting up periodic tasks...')
        
        # Create or get the interval schedule (10 minutes)
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=10,
            period=IntervalSchedule.MINUTES,
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created new interval schedule: every 10 minutes')
            )
        else:
            self.stdout.write('Using existing interval schedule: every 10 minutes')

        # Create or update the periodic task
        task, created = PeriodicTask.objects.get_or_create(
            name='Check Item Count Every 10 Minutes',
            defaults={
                'task': 'core.tasks.check_item_count',
                'interval': schedule,
                'enabled': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created periodic task: Check Item Count Every 10 Minutes')
            )
        else:
            # Update existing task
            task.task = 'core.tasks.check_item_count'
            task.interval = schedule
            task.enabled = True
            task.save()
            self.stdout.write(
                self.style.SUCCESS('Updated periodic task: Check Item Count Every 10 Minutes')
            )
        
        # Optional: Create a low stock check task (every hour)
        hourly_schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.HOURS,
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created new interval schedule: every 1 hour')
            )
        
        low_stock_task, created = PeriodicTask.objects.get_or_create(
            name='Check Low Stock Items Every Hour',
            defaults={
                'task': 'core.tasks.check_low_stock_items',
                'interval': hourly_schedule,
                'enabled': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created periodic task: Check Low Stock Items Every Hour')
            )
        else:
            low_stock_task.task = 'core.tasks.check_low_stock_items'
            low_stock_task.interval = hourly_schedule
            low_stock_task.enabled = True
            low_stock_task.save()
            self.stdout.write(
                self.style.SUCCESS('Updated periodic task: Check Low Stock Items Every Hour')
            )
        
        self.stdout.write(
            self.style.SUCCESS('Periodic tasks setup complete!')
        )
        
        # Display current tasks
        self.stdout.write('\nCurrent periodic tasks:')
        for task in PeriodicTask.objects.filter(enabled=True):
            self.stdout.write(f'  - {task.name}: {task.task} ({task.interval})')
