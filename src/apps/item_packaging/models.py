# Create your models here.
from apps.base.time_stamped_abstract_class import TimeStampedAbstractModelClass
from django.db import models


class ItemPackaging(TimeStampedAbstractModelClass):
    name = models.CharField(max_length=255)
    label = models.CharField(max_length=255, unique=True)
    unit = models.CharField(max_length=255)
    remarks = models.TextField(null=True, blank=True)
    def __str__(self):
        return self.name  # Add this for string representation

    def clean(self):
        self.label = self.label.upper()

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        indexes = [
            models.Index(fields=["label"], name="packaging_label_idx"),
        ]



