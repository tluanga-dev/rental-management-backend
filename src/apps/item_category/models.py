# items/models/categories.py
from django.core.exceptions import ValidationError

from apps.base.time_stamped_abstract_class import TimeStampedAbstractModelClass
from django.db import models


class CategoryBase(TimeStampedAbstractModelClass):
    abbreviation = models.CharField(max_length=9, unique=True)
    description = models.TextField(null=True, blank=True)

    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=["name"]),
        ]

    def clean_upper_case(self, fields):
        """Ensure specified fields are in uppercase."""
        for field in fields:
            value = getattr(self, field, None)
            if value:
                setattr(self, field, value.upper())

    def clean(self):
        self.clean_upper_case(["abbreviation"])
        super().clean()

    def __str__(self):
        return self.name  # Use the name field for string representation


class ItemCategory(CategoryBase):
    name = models.CharField(max_length=255, unique=True)

    class Meta(CategoryBase.Meta):
        verbose_name_plural = "Item Categories"

    def __str__(self):
        return self.name  # Use the name field for string representation


class ItemSubCategory(CategoryBase):
    # Override name to remove global unique constraint
    name = models.CharField(max_length=255, unique=False)
    item_category = models.ForeignKey(
        ItemCategory, on_delete=models.CASCADE, related_name="subcategories"
    )

    class Meta(CategoryBase.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["name", "item_category"],
                name="unique_subcategory_name_per_category",
            )
        ]

    def clean(self):
        super().clean()
        if len(self.abbreviation) != 6:
            raise ValidationError("Abbreviation must be exactly 6 characters.")
        if not any(c.isalpha() for c in self.abbreviation):
            raise ValidationError("Must contain at least one letter.")

    def __str__(self):
        return self.name  # Use the name field for string representation
