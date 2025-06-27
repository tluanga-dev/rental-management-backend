from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from django.utils import timezone
from uuid import uuid4
from apps.base.time_stamped_abstract_class import TimeStampedAbstractModelClass

class TrackingType(models.TextChoices):
    BULK = "BULK", _("Bulk")
    INDIVIDUAL = "INDIVIDUAL", _("Individual")

class InventoryItemMaster(TimeStampedAbstractModelClass):
    """
    Master inventory item model for managing item definitions and specifications
    """
    name = models.CharField(
        _("name"),
        max_length=255,
        unique=True,
        help_text=_("Item name (unique across all items)")
    )
    
    sku = models.CharField(
        _("SKU"),
        max_length=255,
        unique=True,
        help_text=_("Stock Keeping Unit (stored in uppercase, case-insensitive)")
    )
    
    description = models.TextField(
        _("description"),
        blank=True,
        null=True,
        help_text=_("Detailed description of the item")
    )
    
    contents = models.TextField(
        _("contents"),
        blank=True,
        null=True,
        help_text=_("Contents or composition of the item")
    )
    
    item_sub_category = models.ForeignKey(
        'item_category.ItemSubCategory',
        on_delete=models.PROTECT,
        verbose_name=_("subcategory"),
        help_text=_("Item subcategory this item belongs to")
    )
    
    unit_of_measurement = models.ForeignKey(
        'unit_of_measurement.UnitOfMeasurement',
        on_delete=models.PROTECT,
        verbose_name=_("unit of measurement"),
        help_text=_("Unit of measurement for this item")
    )
    
    packaging = models.ForeignKey(
        'item_packaging.ItemPackaging',
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_("packaging"),
        help_text=_("Packaging type for this item")
    )
    
    tracking_type = models.CharField(
        _("tracking type"),
        max_length=20,
        choices=TrackingType.choices,
        help_text=_("Tracking type: BULK or INDIVIDUAL")
    )
    
    is_consumable = models.BooleanField(
        _("is consumable"),
        default=False,
        help_text=_("Whether this item is consumable")
    )
    
    brand = models.CharField(
        _("brand"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Product brand or manufacturer name")
    )
    
    manufacturer_part_number = models.CharField(
        _("manufacturer part number"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Original manufacturer's part number")
    )
    
    product_id = models.CharField(
        _("product ID"),
        max_length=255,
        blank=True,
        null=True,
        help_text=_("Additional product identifier")
    )
    
    weight = models.DecimalField(
        _("weight"),
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text=_("Physical weight in kilograms")
    )
    
    length = models.DecimalField(
        _("length"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text=_("Length dimension in centimeters")
    )
    
    width = models.DecimalField(
        _("width"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text=_("Width dimension in centimeters")
    )
    
    height = models.DecimalField(
        _("height"),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text=_("Height dimension in centimeters")
    )
    
    renting_period = models.PositiveIntegerField(
        _("renting period"),
        default=1,
        validators=[MinValueValidator(1)],
        help_text=_("Default rental period in days")
    )
    
    quantity = models.IntegerField(
        _("quantity"),
        default=0,
        help_text=_("Total physical stock across all warehouses")
    )
    
    class Meta:
        verbose_name = _("Inventory Item Master")
        verbose_name_plural = _("Inventory Item Masters")
        ordering = ['name']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['tracking_type']),
            models.Index(fields=['is_consumable']),
            models.Index(fields=['quantity']),
        ]

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Normalize SKU before saving"""
        if self.sku:
            self.sku = self.sku.strip().upper()
        super().save(*args, **kwargs)


class InventoryItemStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", _("Available")
    RENTED = "RENTED", _("Rented")
    MAINTENANCE = "MAINTENANCE", _("Under Maintenance")
    RETIRED = "RETIRED", _("Retired")
    LOST = "LOST", _("Lost")

class WarrantyPeriodType(models.TextChoices):
    DAYS = "DAYS", _("Days")
    MONTHS = "MONTHS", _("Months")
    YEARS = "YEARS", _("Years")

class InventoryItem(TimeStampedAbstractModelClass):
    """
    Individual inventory item instances or bulk batches
    """
    inventory_item_master = models.ForeignKey(
        'InventoryItemMaster',
        on_delete=models.CASCADE,
        verbose_name=_("master item"),
        related_name='instances',
        help_text=_("Master item definition this instance belongs to")
    )
    
    warehouse = models.ForeignKey(
        'warehouse.Warehouse',
        on_delete=models.PROTECT,
        verbose_name=_("warehouse"),
        help_text=_("Warehouse where this item is located")
    )
    
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=InventoryItemStatus.choices,
        default=InventoryItemStatus.AVAILABLE,
        help_text=_("Current status of the inventory item")
    )
    
    serial_number = models.CharField(
        _("serial number"),
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text=_("Required and unique for individually tracked items")
    )
    
    quantity = models.PositiveIntegerField(
        _("quantity"),
        default=1,
        help_text=_("Quantity for bulk items, must be 1 for individual items")
    )
    
    rental_rate = models.DecimalField(
        _("rental rate"),
        max_digits=12,
        decimal_places=2,
        default=0.0,
        help_text=_("Rental rate per period")
    )
    
    replacement_cost = models.DecimalField(
        _("replacement cost"),
        max_digits=12,
        decimal_places=2,
        default=0.0,
        help_text=_("Cost to replace this item")
    )
    
    late_fee_rate = models.DecimalField(
        _("late fee rate"),
        max_digits=10,
        decimal_places=2,
        default=0.0,
        help_text=_("Late fee rate for overdue rentals")
    )
    
    sell_tax_rate = models.PositiveIntegerField(
        _("sell tax rate"),
        default=0,
        help_text=_("Sales tax rate (percentage * 100)")
    )
    
    rent_tax_rate = models.PositiveIntegerField(
        _("rent tax rate"),
        default=0,
        help_text=_("Rental tax rate (percentage * 100)")
    )
    
    rentable = models.BooleanField(
        _("rentable"),
        default=True,
        help_text=_("Whether this item is available for rent")
    )
    
    sellable = models.BooleanField(
        _("sellable"),
        default=False,
        help_text=_("Whether this item is available for sale")
    )
    
    selling_price = models.DecimalField(
        _("selling price"),
        max_digits=12,
        decimal_places=2,
        default=0.0,
        help_text=_("Selling price of the item")
    )
    
    warranty_period_type = models.CharField(
        _("warranty period type"),
        max_length=20,
        choices=WarrantyPeriodType.choices,
        blank=True,
        null=True,
        help_text=_("Warranty period type")
    )
    
    warranty_period = models.PositiveIntegerField(
        _("warranty period"),
        blank=True,
        null=True,
        help_text=_("Warranty period value")
    )
    
    class Meta:
        verbose_name = _("Inventory Item")
        verbose_name_plural = _("Inventory Items")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['serial_number']),
            models.Index(fields=['rentable', 'sellable']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gte=0),
                name="non_negative_quantity"
            ),
            models.UniqueConstraint(
                fields=['serial_number'],
                condition=models.Q(serial_number__isnull=False),
                name='unique_serial_number'
            )
        ]
    
    def __str__(self):
        if self.serial_number:
            return f"{self.inventory_item_master.name} - {self.serial_number}"
        return f"{self.inventory_item_master.name} - {self.warehouse.name}"


class MovementType(models.TextChoices):
    PURCHASE = "PURCHASE", _("Purchase")
    PURCHASE_RETURN = "PURCHASE_RETURN", _("Purchase Return")
    SELL = "SELL", _("Sell")
    SELL_RETURN = "SELL_RETURN", _("Sell Return")
    RENT = "RENT", _("Rent")
    RENT_RETURN = "RENT_RETURN", _("Rent Return")
    RECONCILIATION = "RECONCILIATION", _("Reconciliation")
    INTER_WAREHOUSE_TRANSFER = "INTER_WAREHOUSE_TRANSFER", _("Inter-Warehouse Transfer")

class InventoryItemStockMovement(TimeStampedAbstractModelClass):
    """
    Track all stock movements for inventory items
    """
    inventory_item = models.ForeignKey(
        'InventoryItem',
        on_delete=models.PROTECT,
        verbose_name=_("inventory item"),
        related_name='movements',
        help_text=_("Inventory item this movement belongs to")
    )
    
    movement_type = models.CharField(
        _("movement type"),
        max_length=30,
        choices=MovementType.choices,
        help_text=_("Type of stock movement")
    )
    
    inventory_transaction_id = models.CharField(
        _("transaction ID"),
        max_length=255,
        help_text=_("Reference to the transaction that caused this movement")
    )
    
    quantity = models.IntegerField(
        _("quantity"),
        help_text=_("Quantity moved (positive for in, negative for out)")
    )
    
    quantity_on_hand_before = models.IntegerField(
        _("quantity before"),
        help_text=_("Stock quantity before this transaction")
    )
    
    quantity_on_hand_after = models.IntegerField(
        _("quantity after"),
        help_text=_("Stock quantity after this transaction")
    )
    
    warehouse_from = models.ForeignKey(
        'warehouse.Warehouse',
        on_delete=models.PROTECT,
        related_name='outgoing_transfers',
        blank=True,
        null=True,
        verbose_name=_("source warehouse"),
        help_text=_("Source warehouse for transfers")
    )
    
    warehouse_to = models.ForeignKey(
        'warehouse.Warehouse',
        on_delete=models.PROTECT,
        related_name='incoming_transfers',
        blank=True,
        null=True,
        verbose_name=_("destination warehouse"),
        help_text=_("Destination warehouse for transfers")
    )
    
    notes = models.TextField(
        _("notes"),
        blank=True,
        null=True,
        help_text=_("Additional notes about the movement")
    )
    
    class Meta:
        verbose_name = _("Stock Movement")
        verbose_name_plural = _("Stock Movements")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['movement_type']),
            models.Index(fields=['inventory_transaction_id']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.inventory_item} - {self.movement_type} - {self.quantity}"