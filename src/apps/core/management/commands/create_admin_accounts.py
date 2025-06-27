"""
Django management command to create admin accounts from admin_accounts.md
"""

import os
import re
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class Command(BaseCommand):
    help = 'Create admin accounts from doc/admin_accounts.md file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='doc/admin_accounts.md',
            help='Path to admin accounts file (default: doc/admin_accounts.md)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if users already exist'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('🔧 Django Admin Account Creator')
        )
        self.stdout.write('=' * 40)
        
        # Parse admin accounts
        accounts = self.parse_admin_accounts_file(file_path)
        
        if not accounts:
            self.stdout.write(
                self.style.WARNING('⚠️  No admin accounts found in the file')
            )
            # Create default admin account
            self.stdout.write('🔧 Creating default admin account...')
            success = self.create_admin_account('admin', 'Aizawl@1234', force=force)
            if success:
                self.stdout.write(
                    self.style.SUCCESS('✅ Default admin account created successfully')
                )
            return
        
        self.stdout.write(f'📋 Found {len(accounts)} admin account(s) to process')
        
        # Create each admin account
        created_count = 0
        for account in accounts:
            username = account['username']
            password = account['password']
            
            self.stdout.write(f'\n🔨 Processing admin user: {username}')
            
            if self.create_admin_account(username, password, force=force):
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Admin account creation completed!')
        )
        self.stdout.write(
            f'📊 Summary: {created_count} new admin account(s) created, '
            f'{len(accounts) - created_count} already existed'
        )

    def parse_admin_accounts_file(self, file_path):
        """Parse the admin_accounts.md file to extract admin credentials."""
        accounts = []
        
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.WARNING(f'⚠️  Admin accounts file not found: {file_path}')
            )
            return accounts
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Remove HTML comments and commented lines
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
            
            # Split into lines and process
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            current_account = {}
            
            for line in lines:
                # Skip empty lines and markdown headers
                if not line or line.startswith('#') or line.startswith('admin accounts detail'):
                    continue
                
                # Look for username pattern
                username_match = re.search(r'(?:admin\s+)?user\s*name\s*:\s*(.+)', line, re.IGNORECASE)
                if username_match:
                    if current_account and 'username' in current_account and 'password' in current_account:
                        accounts.append(current_account)
                        current_account = {}
                    current_account['username'] = username_match.group(1).strip()
                    continue
                
                # Look for password pattern
                password_match = re.search(r'password\s*:\s*(.+)', line, re.IGNORECASE)
                if password_match:
                    current_account['password'] = password_match.group(1).strip()
                    continue
            
            # Add the last account if complete
            if current_account and 'username' in current_account and 'password' in current_account:
                accounts.append(current_account)
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error reading admin accounts file: {e}')
            )
            return []
        
        return accounts

    def create_admin_account(self, username, password, email=None, force=False):
        """Create a Django superuser account if it doesn't exist."""
        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                if not force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'ℹ️  Admin user \'{username}\' already exists - skipping creation'
                        )
                    )
                    return False
                else:
                    # Delete existing user if force is True
                    User.objects.filter(username=username).delete()
                    self.stdout.write(
                        self.style.WARNING(f'🔄 Deleted existing user \'{username}\'')
                    )
            
            # Create superuser
            if not email:
                email = f"{username}@admin.local"
            
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully created admin user \'{username}\'')
            )
            return True
            
        except ValidationError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Validation error creating user \'{username}\': {e}')
            )
            return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error creating admin user \'{username}\': {e}')
            )
            return False
