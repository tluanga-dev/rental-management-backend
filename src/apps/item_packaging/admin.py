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
from .models import ItemPackaging


@admin.register(ItemPackaging)
class ItemPackagingAdmin(admin.ModelAdmin):
    """Admin interface for Item Packaging model with CSV import functionality."""
    list_display = ('name', 'label', 'unit', 'created_at', 'updated_at')
    list_filter = ('unit', 'created_at', 'updated_at')
    search_fields = ('name', 'label', 'unit', 'remarks')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ['export_to_csv']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'label', 'unit')
        }),
        ('Additional Information', {
            'fields': ('remarks',)
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
            path('import-csv/', self.admin_site.admin_view(self.import_csv), name='item_packaging_import_csv'),
            path('load-predefined/', self.admin_site.admin_view(self.load_predefined_data), name='item_packaging_load_predefined'),
            path('download-csv-template/', self.admin_site.admin_view(self.download_csv_template), name='item_packaging_csv_template'),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        """Add import buttons to the changelist view."""
        extra_context = extra_context or {}
        extra_context['import_csv_url'] = 'admin:item_packaging_import_csv'
        extra_context['load_predefined_url'] = 'admin:item_packaging_load_predefined'
        extra_context['csv_template_url'] = 'admin:item_packaging_csv_template'
        return super().changelist_view(request, extra_context=extra_context)

    def import_csv(self, request):
        """Handle CSV file import."""
        if request.method == 'POST':
            csv_file = request.FILES.get('csv_file')
            if not csv_file:
                messages.error(request, 'Please select a CSV file to upload.')
                return redirect('admin:item_packaging_itempackaging_changelist')
            
            if not csv_file.name.endswith('.csv'):
                messages.error(request, 'Please upload a valid CSV file.')
                return redirect('admin:item_packaging_itempackaging_changelist')
            
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
                        label = row.get('label', '').strip()
                        unit = row.get('unit', '').strip()
                        remarks = row.get('remarks', '').strip()
                        
                        if not name or not label or not unit:
                            errors.append(f"Row {row_num}: Name, label, and unit are required")
                            error_count += 1
                            continue
                        
                        # Check if packaging already exists (by label since it's unique)
                        existing_packaging = ItemPackaging.objects.filter(label__iexact=label).first()
                        
                        if existing_packaging:
                            # Update existing packaging
                            existing_packaging.name = name
                            existing_packaging.label = label.upper()
                            existing_packaging.unit = unit
                            existing_packaging.remarks = remarks if remarks else existing_packaging.remarks
                            existing_packaging.save()
                            updated_count += 1
                        else:
                            # Create new packaging
                            ItemPackaging.objects.create(
                                name=name,
                                label=label.upper(),
                                unit=unit,
                                remarks=remarks
                            )
                            created_count += 1
                            
                    except Exception as e:
                        errors.append(f"Row {row_num}: {str(e)}")
                        error_count += 1
                
                # Show results
                if created_count > 0:
                    messages.success(request, f'Successfully created {created_count} packaging types.')
                if updated_count > 0:
                    messages.success(request, f'Successfully updated {updated_count} packaging types.')
                if error_count > 0:
                    error_msg = f'{error_count} errors occurred during import:'
                    for error in errors[:10]:  # Show first 10 errors
                        error_msg += f'\n• {error}'
                    if len(errors) > 10:
                        error_msg += f'\n... and {len(errors) - 10} more errors.'
                    messages.error(request, error_msg)
                
            except Exception as e:
                messages.error(request, f'Error processing CSV file: {str(e)}')
            
            return redirect('admin:item_packaging_itempackaging_changelist')
        
        # GET request - show import form
        context = {
            'title': 'Import Packaging Types from CSV',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return TemplateResponse(request, 'admin/item_packaging/import_csv.html', context)

    def load_predefined_data(self, request):
        """Load predefined data from JSON file."""
        if request.method == 'POST':
            try:
                # Path to the JSON file
                json_file_path = os.path.join(settings.BASE_DIR.parent, 'data', 'item_packaging.json')
                
                if not os.path.exists(json_file_path):
                    messages.error(request, 'Predefined data file not found.')
                    return redirect('admin:item_packaging_itempackaging_changelist')
                
                with open(json_file_path, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                created_count = 0
                updated_count = 0
                
                # Process packaging data
                packaging_list = data if isinstance(data, list) else data.get('packaging_types', [])
                
                for packaging_data in packaging_list:
                    name = packaging_data.get('name', '').strip()
                    label = packaging_data.get('label', '').strip()
                    unit = packaging_data.get('unit', '').strip()
                    remarks = packaging_data.get('remarks', '').strip()
                    
                    if not name or not label or not unit:
                        continue
                    
                    # Check if packaging already exists
                    existing_packaging = ItemPackaging.objects.filter(label__iexact=label).first()
                    
                    if existing_packaging:
                        # Update existing packaging
                        existing_packaging.name = name
                        existing_packaging.label = label.upper()
                        existing_packaging.unit = unit
                        if remarks:
                            existing_packaging.remarks = remarks
                        existing_packaging.save()
                        updated_count += 1
                    else:
                        # Create new packaging
                        ItemPackaging.objects.create(
                            name=name,
                            label=label.upper(),
                            unit=unit,
                            remarks=remarks
                        )
                        created_count += 1
                
                if created_count > 0:
                    messages.success(request, f'Successfully created {created_count} packaging types from predefined data.')
                if updated_count > 0:
                    messages.success(request, f'Successfully updated {updated_count} packaging types from predefined data.')
                if created_count == 0 and updated_count == 0:
                    messages.info(request, 'No new packaging types were created. All predefined types already exist.')
                
            except Exception as e:
                messages.error(request, f'Error loading predefined data: {str(e)}')
            
            return redirect('admin:item_packaging_itempackaging_changelist')
        
        # GET request - show confirmation form
        context = {
            'title': 'Load Predefined Packaging Types',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        return TemplateResponse(request, 'admin/item_packaging/load_predefined.html', context)

    def download_csv_template(self, request):
        """Download a CSV template file."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="item_packaging_template.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['name', 'label', 'unit', 'remarks'])
        writer.writerow(['Box', 'BOX', 'box', 'Standard cardboard box for small items'])
        writer.writerow(['Pallet', 'PLT', 'pallet', 'Wooden pallet for heavy items'])
        writer.writerow(['Bag', 'BAG', 'bag', 'Plastic or fabric bag for loose items'])
        writer.writerow(['Crate', 'CRT', 'crate', 'Wooden or plastic crate for fragile items'])
        
        return response

    def export_to_csv(self, request, queryset):
        """Export selected packaging types to CSV."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="item_packaging.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['name', 'label', 'unit', 'remarks', 'created_at', 'updated_at'])
        
        for packaging in queryset:
            writer.writerow([
                packaging.name,
                packaging.label,
                packaging.unit,
                packaging.remarks or '',
                packaging.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                packaging.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response
    
    export_to_csv.short_description = "Export selected packaging types to CSV"
