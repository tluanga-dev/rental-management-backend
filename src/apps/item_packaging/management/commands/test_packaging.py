from django.core.management.base import BaseCommand
from django.conf import settings
from item_packaging.models import ItemPackaging
import json
import os
import csv
import io


class Command(BaseCommand):
    help = 'Test and load packaging data'

    def add_arguments(self, parser):
        parser.add_argument('--test-csv', action='store_true', help='Test CSV import functionality')
        parser.add_argument('--load-predefined', action='store_true', help='Load predefined packaging data from JSON')
        parser.add_argument('--clear-data', action='store_true', help='Clear existing packaging data')
        parser.add_argument('--show-data', action='store_true', help='Show current packaging data')

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🧪 Testing Item Packaging Admin Functionality'))
        self.stdout.write('=' * 60)

        if options['clear_data']:
            self.clear_data()

        if options['test_csv']:
            self.test_csv_import()

        if options['load_predefined']:
            self.load_predefined_data()

        if options['show_data']:
            self.show_data()

    def clear_data(self):
        count = ItemPackaging.objects.count()
        ItemPackaging.objects.all().delete()
        self.stdout.write(self.style.WARNING(f'🗑️  Cleared {count} existing packaging items'))

    def test_csv_import(self):
        self.stdout.write('\n📋 Testing CSV Import Functionality')
        self.stdout.write('-' * 40)

        csv_data = """name,label,unit,remarks
Test Standard Box,TSTD,box,Standard test box for testing
Test Heavy Pallet,THVY,pallet,Heavy test pallet for testing
Test Plastic Bag,TPBG,bag,Plastic test bag for testing
Test Steel Crate,TSTL,crate,Steel test crate for testing"""

        self.stdout.write('📄 Created test CSV data:')
        for line in csv_data.split('\n'):
            self.stdout.write(f'  {line}')

        io_string = io.StringIO(csv_data)
        reader = csv.DictReader(io_string)

        created_count = 0
        updated_count = 0

        for row in reader:
            name = row.get('name', '').strip()
            label = row.get('label', '').strip()
            unit = row.get('unit', '').strip()
            remarks = row.get('remarks', '').strip()

            if not name or not label or not unit:
                continue

            existing_packaging = ItemPackaging.objects.filter(label__iexact=label).first()

            if existing_packaging:
                existing_packaging.name = name
                existing_packaging.label = label.upper()
                existing_packaging.unit = unit
                existing_packaging.remarks = remarks
                existing_packaging.save()
                updated_count += 1
                self.stdout.write(f'🔄 Updated: {name} ({label})')
            else:
                ItemPackaging.objects.create(
                    name=name,
                    label=label.upper(),
                    unit=unit,
                    remarks=remarks
                )
                created_count += 1
                self.stdout.write(f'✅ Created: {name} ({label})')

        self.stdout.write(self.style.SUCCESS(f'📊 CSV Import Results: {created_count} created, {updated_count} updated'))

    def load_predefined_data(self):
        self.stdout.write('\n📦 Loading Predefined Packaging Data')
        self.stdout.write('-' * 40)

        json_file_path = os.path.join(settings.BASE_DIR.parent, 'data', 'item_packaging.json')

        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'❌ JSON file not found: {json_file_path}'))
            return

        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            created_count = 0
            updated_count = 0

            packaging_list = data if isinstance(data, list) else data.get('packaging_types', [])

            for packaging_data in packaging_list:
                name = packaging_data.get('name', '').strip()
                label = packaging_data.get('label', '').strip()
                unit = packaging_data.get('unit', '').strip()
                remarks = packaging_data.get('remarks', '').strip()

                if not name or not label or not unit:
                    continue

                existing_packaging = ItemPackaging.objects.filter(label__iexact=label).first()

                if existing_packaging:
                    existing_packaging.name = name
                    existing_packaging.label = label.upper()
                    existing_packaging.unit = unit
                    if remarks:
                        existing_packaging.remarks = remarks
                    existing_packaging.save()
                    updated_count += 1
                    self.stdout.write(f'🔄 Updated: {name} ({label})')
                else:
                    ItemPackaging.objects.create(
                        name=name,
                        label=label.upper(),
                        unit=unit,
                        remarks=remarks
                    )
                    created_count += 1
                    self.stdout.write(f'✅ Created: {name} ({label})')

            self.stdout.write(self.style.SUCCESS(f'📊 Predefined Data Results: {created_count} created, {updated_count} updated'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error loading predefined data: {str(e)}'))

    def show_data(self):
        self.stdout.write('\n📦 Current Packaging Data')
        self.stdout.write('-' * 40)

        items = ItemPackaging.objects.all().order_by('name')
        count = items.count()

        if count == 0:
            self.stdout.write('📭 No packaging items found')
            return

        self.stdout.write(f'📊 Total packaging types: {count}')
        self.stdout.write('')

        for item in items:
            remarks = item.remarks[:50] + '...' if item.remarks and len(item.remarks) > 50 else item.remarks or ''
            self.stdout.write(f'  • {item.name} ({item.label}) - {item.unit}')
            if remarks:
                self.stdout.write(f'    ↳ {remarks}')

        self.stdout.write('\n📈 Summary by Unit:')
        units = items.values_list('unit', flat=True)
        unit_counts = {}
        for unit in units:
            unit_counts[unit] = unit_counts.get(unit, 0) + 1

        for unit, count in sorted(unit_counts.items()):
            self.stdout.write(f'  • {unit}: {count} types')
