from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.base.time_stamped_abstract_class import TimeStampedAbstractModelClass


class WarrantyPeriodTypeChoices(models.TextChoices):
    DAYS = "DAYS", _("Days")
    MONTHS = "MONTHS", _("Months")
    YEARS = "YEARS", _("Years")


class PurchaseTransaction(TimeStampedAbstractModelClass):
    transaction_date = models.DateField()
    transaction_id = models.CharField(max_length=20, unique=True, editable=False, db_index=True)
    vendor = models.ForeignKey(
        'vendor.Vendor', 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True
    )
    reference_number = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    invoice_number = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    total_tax_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, default=0)
    total_discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, default=0)
    remarks = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name = _("Purchase Transaction")
        verbose_name_plural = _("Purchase Transactions")
        ordering = ['-transaction_date', '-created_at']
        indexes = [
            models.Index(fields=['transaction_date']),
            models.Index(fields=['transaction_id']),
            models.Index(fields=['reference_number']),
            models.Index(fields=['invoice_number']),
        ]
    
    def __str__(self):
        return f"Purchase {self.transaction_id} - {self.transaction_date}"


class PurchaseTransactionItem(TimeStampedAbstractModelClass):
    transaction = models.ForeignKey(
        PurchaseTransaction, 
        on_delete=models.CASCADE, 
        related_name="transaction_items"
    )
    inventory_item = models.ForeignKey(
        'inventory_item.LineItem', 
        on_delete=models.PROTECT, 
        related_name="transaction_line_items"
    )
    serial_number = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reference_number = models.CharField(max_length=255, null=True, blank=True)
    warranty_period_type = models.CharField(
        max_length=20,
        choices=WarrantyPeriodTypeChoices.choices,
        default=WarrantyPeriodTypeChoices.YEARS,
        db_index=True,
        help_text=_("Warranty period type"),
        null=True,
        blank=True
    )
    warranty_period = models.PositiveIntegerField(null=True, blank=True)
    
    class Meta:
        verbose_name = _("Purchase Transaction Item")
        verbose_name_plural = _("Purchase Transaction Items")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['serial_number']),
            models.Index(fields=['reference_number']),
        ]
    
    def __str__(self):
        return f"{self.transaction.transaction_id} - {self.inventory_item} - Qty: {self.quantity}"
