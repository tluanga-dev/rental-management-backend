# Generated by Django 4.2.17 on 2025-06-26 20:48

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('warehouse', '0001_initial'),
        ('unit_of_measurement', '0001_initial'),
        ('item_category', '0001_initial'),
        ('item_packaging', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InventoryItemMaster',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('name', models.CharField(help_text='Item name (unique across all items)', max_length=255, unique=True, verbose_name='name')),
                ('sku', models.CharField(help_text='Stock Keeping Unit (stored in uppercase, case-insensitive)', max_length=255, unique=True, verbose_name='SKU')),
                ('description', models.TextField(blank=True, help_text='Detailed description of the item', null=True, verbose_name='description')),
                ('contents', models.TextField(blank=True, help_text='Contents or composition of the item', null=True, verbose_name='contents')),
                ('tracking_type', models.CharField(choices=[('BULK', 'Bulk'), ('INDIVIDUAL', 'Individual')], help_text='Tracking type: BULK or INDIVIDUAL', max_length=20, verbose_name='tracking type')),
                ('is_consumable', models.BooleanField(default=False, help_text='Whether this item is consumable', verbose_name='is consumable')),
                ('brand', models.CharField(blank=True, help_text='Product brand or manufacturer name', max_length=255, null=True, verbose_name='brand')),
                ('manufacturer_part_number', models.CharField(blank=True, help_text="Original manufacturer's part number", max_length=255, null=True, verbose_name='manufacturer part number')),
                ('product_id', models.CharField(blank=True, help_text='Additional product identifier', max_length=255, null=True, verbose_name='product ID')),
                ('weight', models.DecimalField(blank=True, decimal_places=3, help_text='Physical weight in kilograms', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='weight')),
                ('length', models.DecimalField(blank=True, decimal_places=2, help_text='Length dimension in centimeters', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='length')),
                ('width', models.DecimalField(blank=True, decimal_places=2, help_text='Width dimension in centimeters', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='width')),
                ('height', models.DecimalField(blank=True, decimal_places=2, help_text='Height dimension in centimeters', max_digits=10, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='height')),
                ('renting_period', models.PositiveIntegerField(default=1, help_text='Default rental period in days', validators=[django.core.validators.MinValueValidator(1)], verbose_name='renting period')),
                ('quantity', models.IntegerField(default=0, help_text='Total physical stock across all warehouses', verbose_name='quantity')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('item_sub_category', models.ForeignKey(help_text='Item subcategory this item belongs to', on_delete=django.db.models.deletion.PROTECT, to='item_category.itemsubcategory', verbose_name='subcategory')),
                ('packaging', models.ForeignKey(blank=True, help_text='Packaging type for this item', null=True, on_delete=django.db.models.deletion.PROTECT, to='item_packaging.itempackaging', verbose_name='packaging')),
                ('unit_of_measurement', models.ForeignKey(help_text='Unit of measurement for this item', on_delete=django.db.models.deletion.PROTECT, to='unit_of_measurement.unitofmeasurement', verbose_name='unit of measurement')),
            ],
            options={
                'verbose_name': 'Inventory Item Master',
                'verbose_name_plural': 'Inventory Item Masters',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='InventoryItem',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('status', models.CharField(choices=[('AVAILABLE', 'Available'), ('RENTED', 'Rented'), ('MAINTENANCE', 'Under Maintenance'), ('RETIRED', 'Retired'), ('LOST', 'Lost')], default='AVAILABLE', help_text='Current status of the inventory item', max_length=20, verbose_name='status')),
                ('serial_number', models.CharField(blank=True, help_text='Required and unique for individually tracked items', max_length=255, null=True, unique=True, verbose_name='serial number')),
                ('quantity', models.PositiveIntegerField(default=1, help_text='Quantity for bulk items, must be 1 for individual items', verbose_name='quantity')),
                ('rental_rate', models.DecimalField(decimal_places=2, default=0.0, help_text='Rental rate per period', max_digits=12, verbose_name='rental rate')),
                ('replacement_cost', models.DecimalField(decimal_places=2, default=0.0, help_text='Cost to replace this item', max_digits=12, verbose_name='replacement cost')),
                ('late_fee_rate', models.DecimalField(decimal_places=2, default=0.0, help_text='Late fee rate for overdue rentals', max_digits=10, verbose_name='late fee rate')),
                ('sell_tax_rate', models.PositiveIntegerField(default=0, help_text='Sales tax rate (percentage * 100)', verbose_name='sell tax rate')),
                ('rent_tax_rate', models.PositiveIntegerField(default=0, help_text='Rental tax rate (percentage * 100)', verbose_name='rent tax rate')),
                ('rentable', models.BooleanField(default=True, help_text='Whether this item is available for rent', verbose_name='rentable')),
                ('sellable', models.BooleanField(default=False, help_text='Whether this item is available for sale', verbose_name='sellable')),
                ('selling_price', models.DecimalField(decimal_places=2, default=0.0, help_text='Selling price of the item', max_digits=12, verbose_name='selling price')),
                ('warranty_period_type', models.CharField(blank=True, choices=[('DAYS', 'Days'), ('MONTHS', 'Months'), ('YEARS', 'Years')], help_text='Warranty period type', max_length=20, null=True, verbose_name='warranty period type')),
                ('warranty_period', models.PositiveIntegerField(blank=True, help_text='Warranty period value', null=True, verbose_name='warranty period')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('inventory_item_master', models.ForeignKey(help_text='Master item definition this instance belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='instances', to='inventory_item.inventoryitemmaster', verbose_name='master item')),
                ('warehouse', models.ForeignKey(help_text='Warehouse where this item is located', on_delete=django.db.models.deletion.PROTECT, to='warehouse.warehouse', verbose_name='warehouse')),
            ],
            options={
                'verbose_name': 'Inventory Item',
                'verbose_name_plural': 'Inventory Items',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='InventoryItemStockMovement',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('movement_type', models.CharField(choices=[('PURCHASE', 'Purchase'), ('PURCHASE_RETURN', 'Purchase Return'), ('SELL', 'Sell'), ('SELL_RETURN', 'Sell Return'), ('RENT', 'Rent'), ('RENT_RETURN', 'Rent Return'), ('RECONCILIATION', 'Reconciliation'), ('INTER_WAREHOUSE_TRANSFER', 'Inter-Warehouse Transfer')], help_text='Type of stock movement', max_length=30, verbose_name='movement type')),
                ('inventory_transaction_id', models.CharField(help_text='Reference to the transaction that caused this movement', max_length=255, verbose_name='transaction ID')),
                ('quantity', models.IntegerField(help_text='Quantity moved (positive for in, negative for out)', verbose_name='quantity')),
                ('quantity_on_hand_before', models.IntegerField(help_text='Stock quantity before this transaction', verbose_name='quantity before')),
                ('quantity_on_hand_after', models.IntegerField(help_text='Stock quantity after this transaction', verbose_name='quantity after')),
                ('notes', models.TextField(blank=True, help_text='Additional notes about the movement', null=True, verbose_name='notes')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('inventory_item', models.ForeignKey(help_text='Inventory item this movement belongs to', on_delete=django.db.models.deletion.PROTECT, related_name='movements', to='inventory_item.inventoryitem', verbose_name='inventory item')),
                ('warehouse_from', models.ForeignKey(blank=True, help_text='Source warehouse for transfers', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='outgoing_transfers', to='warehouse.warehouse', verbose_name='source warehouse')),
                ('warehouse_to', models.ForeignKey(blank=True, help_text='Destination warehouse for transfers', null=True, on_delete=django.db.models.deletion.PROTECT, related_name='incoming_transfers', to='warehouse.warehouse', verbose_name='destination warehouse')),
            ],
            options={
                'verbose_name': 'Stock Movement',
                'verbose_name_plural': 'Stock Movements',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['movement_type'], name='inventory_i_movemen_ff630a_idx'), models.Index(fields=['inventory_transaction_id'], name='inventory_i_invento_06f662_idx'), models.Index(fields=['created_at'], name='inventory_i_created_758f4a_idx')],
            },
        ),
        migrations.AddIndex(
            model_name='inventoryitemmaster',
            index=models.Index(fields=['sku'], name='inventory_i_sku_39741a_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitemmaster',
            index=models.Index(fields=['tracking_type'], name='inventory_i_trackin_058291_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitemmaster',
            index=models.Index(fields=['is_consumable'], name='inventory_i_is_cons_b26907_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitemmaster',
            index=models.Index(fields=['quantity'], name='inventory_i_quantit_4e35af_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['status'], name='inventory_i_status_931a62_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['serial_number'], name='inventory_i_serial__3ff198_idx'),
        ),
        migrations.AddIndex(
            model_name='inventoryitem',
            index=models.Index(fields=['rentable', 'sellable'], name='inventory_i_rentabl_56f0e1_idx'),
        ),
        migrations.AddConstraint(
            model_name='inventoryitem',
            constraint=models.CheckConstraint(check=models.Q(('quantity__gte', 0)), name='non_negative_quantity'),
        ),
        migrations.AddConstraint(
            model_name='inventoryitem',
            constraint=models.UniqueConstraint(condition=models.Q(('serial_number__isnull', False)), fields=('serial_number',), name='unique_serial_number'),
        ),
    ]
