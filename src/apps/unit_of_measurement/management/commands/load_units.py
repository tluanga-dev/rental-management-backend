import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import models
from unit_of_measurement.models import UnitOfMeasurement


class Command(BaseCommand):
    help = 'Load predefined units of measurement from JSON file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to JSON file (default: data/unit_of_measurement.json)',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing units if they already exist',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing',
        )

    def handle(self, *args, **options):
        # Determine file path
        if options['file']:
            json_file_path = options['file']
        else:
            json_file_path = os.path.join(settings.BASE_DIR.parent, 'data', 'unit_of_measurement.json')
        
        if not os.path.exists(json_file_path):
            raise CommandError(f'JSON file not found: {json_file_path}')
        
        self.stdout.write(f'Loading data from: {json_file_path}')
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except Exception as e:
            raise CommandError(f'Error reading JSON file: {e}')
        
        created_count = 0
        updated_count = 0
        skipped_count = 0
        
        for category, units in data.items():
            self.stdout.write(f'\nProcessing category: {category}')
            
            for unit_data in units:
                name = unit_data.get('name', '').strip()
                abbreviation = unit_data.get('abbreviation', '').strip()
                description = unit_data.get('description', '').strip()
                
                if not name or not abbreviation:
                    self.stdout.write(
                        self.style.WARNING(f'  Skipping invalid unit: {unit_data}')
                    )
                    skipped_count += 1
                    continue
                
                # Check if unit already exists
                existing_unit = UnitOfMeasurement.objects.filter(
                    models.Q(name__iexact=name) | models.Q(abbreviation__iexact=abbreviation)
                ).first()
                
                if options['dry_run']:
                    if existing_unit:
                        self.stdout.write(f'  Would update: {name} ({abbreviation})')
                    else:
                        self.stdout.write(f'  Would create: {name} ({abbreviation})')
                    continue
                
                if existing_unit:
                    if options['update']:
                        # Update existing unit
                        existing_unit.name = name
                        existing_unit.abbreviation = abbreviation
                        existing_unit.description = description
                        existing_unit.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'  Updated: {name} ({abbreviation})')
                        )
                        updated_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'  Skipped existing: {name} ({abbreviation})')
                        )
                        skipped_count += 1
                else:
                    # Create new unit
                    UnitOfMeasurement.objects.create(
                        name=name,
                        abbreviation=abbreviation,
                        description=description
                    )
                    self.stdout.write(
                        self.style.SUCCESS(f'  Created: {name} ({abbreviation})')
                    )
                    created_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes were made'))
        else:
            self.stdout.write(self.style.SUCCESS('Import completed!'))
        
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Skipped: {skipped_count}')
        
        if not options['dry_run'] and skipped_count > 0 and not options['update']:
            self.stdout.write(
                self.style.WARNING(
                    'Tip: Use --update flag to update existing units instead of skipping them'
                )
            )
