import csv
import io
import json
import os
from django.contrib import admin, messages
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.utils.html import format_html
from django.conf import settings
from django.db import models
from .models import UnitOfMeasurement


@admin.register(UnitOfMeasurement)
class UnitOfMeasurementAdmin(admin.ModelAdmin):
    """Admin interface for Unit of Measurement model with CSV import functionality."""
    list_display = ('name', 'abbreviation', 'description', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'abbreviation', 'description')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['export_to_csv']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'abbreviation', 'description')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        """Add custom URLs for import functionality."""
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='unit_of_measurement_import_csv'),
            path('load-predefined/', self.admin_site.admin_view(self.load_predefined_data), name='unit_of_measurement_load_predefined'),
            path('download-csv-template/', self.admin_site.admin_view(self.download_csv_template), name='unit_of_measurement_csv_template'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Add import buttons to the changelist view."""
        extra_context = extra_context or {}
        extra_context['import_csv_url'] = 'admin:unit_of_measurement_import_csv'
        extra_context['load_predefined_url'] = 'admin:unit_of_measurement_load_predefined'
        extra_context['csv_template_url'] = 'admin:unit_of_measurement_csv_template'
        return super().changelist_view(request, extra_context=extra_context)

    def import_csv(self, request):
        """Handle CSV file import."""
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                messages.error(request, 'Please select a CSV file to upload.')
                return redirect('admin:unit_of_measurement_unitofmeasurement_changelist')
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect('admin:unit_of_measurement_unitofmeasurement_changelist')
            
            try:
                # Read and decode the CSV file
                data_set = csv_file.read().decode('UTF-8')
                io_string = io.StringIO(data_set)
                reader = csv.DictReader(io_string)
                
                created_count = 0
                updated_count = 0
                error_count = 0
                errors = []
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 because row 1 is header
                    try:
                        name = row.get('name', '').strip()
                        abbreviation = row.get('abbreviation', '').strip()
                        description = row.get('description', '').strip()
                        
                        if not name or not abbreviation:
                            errors.append(f"Row {row_num}: Name and abbreviation are required")
                            error_count += 1
                            continue
                        
                        # Check if unit already exists (by name or abbreviation)
                        existing_unit = UnitOfMeasurement.objects.filter(
                            models.Q(name__iexact=name) | models.Q(abbreviation__iexact=abbreviation)
                        ).first()
                        
                        if existing_unit:
                            # Update existing unit
                            existing_unit.name = name
                            existing_unit.abbreviation = abbreviation
                            existing_unit.description = description
                            existing_unit.save()
                            updated_count += 1
                        else:
                            # Create new unit
                            UnitOfMeasurement.objects.create(
                                name=name,
                                abbreviation=abbreviation,
                                description=description
                            )
                            created_count += 1
                            
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        error_count += 1
                
                # Show results
                if created_count > 0:
                    messages.success(request, f'Successfully created {created_count} units of measurement.')
                if updated_count > 0:
                    messages.success(request, f'Successfully updated {updated_count} units of measurement.')
                if error_count > 0:
                    error_msg = f'{error_count} errors occurred during import:'
                    for error in errors[:10]:  # Show first 10 errors
                        error_msg += f'\n• {error}'
                    if len(errors) > 10:
                        error_msg += f'\n... and {len(errors) - 10} more errors.'
                    messages.error(request, error_msg)
                
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
            
            return redirect('admin:unit_of_measurement_unitofmeasurement_changelist')
        
        # GET request - show import form
        context = {
            'title': 'Import Units of Measurement from CSV',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return TemplateResponse(request, 'admin/unit_of_measurement/import_csv.html', context)

    def load_predefined_data(self, request):
        """Load predefined data from JSON file."""
        if request.method == 'POST':
            try:
                # Path to the JSON file
                json_file_path = os.path.join(settings.BASE_DIR.parent, 'data', 'unit_of_measurement.json')
                
                if not os.path.exists(json_file_path):
                    messages.error(request, 'Predefined data file not found.')
                    return redirect('admin:unit_of_measurement_unitofmeasurement_changelist')
                
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                created_count = 0
                updated_count = 0
                
                # Process all categories of units
                for category, units in data.items():
                    for unit_data in units:
                        name = unit_data.get('name', '').strip()
                        abbreviation = unit_data.get('abbreviation', '').strip()
                        description = unit_data.get('description', '').strip()
                        
                        if not name or not abbreviation:
                            continue
                        
                        # Check if unit already exists
                        existing_unit = UnitOfMeasurement.objects.filter(
                            models.Q(name__iexact=name) | models.Q(abbreviation__iexact=abbreviation)
                        ).first()
                        
                        if existing_unit:
                            # Update existing unit
                            existing_unit.name = name
                            existing_unit.abbreviation = abbreviation
                            existing_unit.description = description
                            existing_unit.save()
                            updated_count += 1
                        else:
                            # Create new unit
                            UnitOfMeasurement.objects.create(
                                name=name,
                                abbreviation=abbreviation,
                                description=description
                            )
                            created_count += 1
                
                if created_count > 0:
                    messages.success(request, f'Successfully created {created_count} units of measurement from predefined data.')
                if updated_count > 0:
                    messages.success(request, f'Successfully updated {updated_count} units of measurement from predefined data.')
                if created_count == 0 and updated_count == 0:
                    messages.info(request, 'No new units were created. All predefined units already exist.')
                
            except Exception as e:
                messages.error(request, f'Error loading predefined data: {str(e)}')
            
            return redirect('admin:unit_of_measurement_unitofmeasurement_changelist')
        
        # GET request - show confirmation form
        context = {
            'title': 'Load Predefined Units of Measurement',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return TemplateResponse(request, 'admin/unit_of_measurement/load_predefined.html', context)

    def download_csv_template(self, request):
        """Download a CSV template file."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="unit_of_measurement_template.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['name', 'abbreviation', 'description'])
        writer.writerow(['Kilogram', 'kg', 'Standard metric weight unit for bulk items'])
        writer.writerow(['Piece', 'pc', 'Standard unit for individual items'])
        writer.writerow(['Liter', 'L', 'Standard metric volume unit for liquids'])
        
        return response

    def export_to_csv(self, request, queryset):
        """Export selected units to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="units_of_measurement.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['name', 'abbreviation', 'description', 'created_at', 'updated_at'])
        
        for unit in queryset:
            writer.writerow([
                unit.name,
                unit.abbreviation,
                unit.description,
                unit.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                unit.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    
    export_to_csv.short_description = "Export selected units to CSV"
