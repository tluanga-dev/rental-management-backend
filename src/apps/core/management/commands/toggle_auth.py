"""
Management command to toggle authentication on/off for development.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os


class Command(BaseCommand):
    help = 'Toggle authentication on/off for development purposes'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            type=str,
            choices=['enable', 'disable', 'status'],
            help='Action to perform: enable, disable, or status'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'status':
            self.show_status()
        elif action == 'enable':
            self.enable_authentication()
        elif action == 'disable':
            self.disable_authentication()

    def show_status(self):
        """Show current authentication status."""
        enable_auth = getattr(settings, 'ENABLE_AUTHENTICATION', True)
        env_value = os.environ.get('ENABLE_AUTHENTICATION', 'True')
        
        self.stdout.write(
            self.style.SUCCESS(f"Current Authentication Status:")
        )
        self.stdout.write(f"  Environment Variable: ENABLE_AUTHENTICATION={env_value}")
        self.stdout.write(f"  Effective Setting: {enable_auth}")
        
        if enable_auth:
            self.stdout.write(
                self.style.WARNING("🔐 Authentication is ENABLED - API requires JWT tokens")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("🔓 Authentication is DISABLED - API allows anonymous access")
            )

    def enable_authentication(self):
        """Enable authentication."""
        self.stdout.write("To enable authentication, set environment variable:")
        self.stdout.write(
            self.style.SUCCESS("export ENABLE_AUTHENTICATION=True")
        )
        self.stdout.write("Or for Railway deployment, set in environment variables:")
        self.stdout.write("ENABLE_AUTHENTICATION=True")
        
    def disable_authentication(self):
        """Disable authentication.""" 
        self.stdout.write("To disable authentication for development, set environment variable:")
        self.stdout.write(
            self.style.WARNING("export ENABLE_AUTHENTICATION=False")
        )
        self.stdout.write(
            self.style.WARNING("⚠️  WARNING: This disables security - use only for development!")
        )
