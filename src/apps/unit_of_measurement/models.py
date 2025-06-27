
# Create your models here.
from apps.base.time_stamped_abstract_class import TimeStampedAbstractModelClass
from django.db import models
from django.core.exceptions import ValidationError




class UnitOfMeasurement(TimeStampedAbstractModelClass):
    name = models.CharField(max_length=255, unique=True)
    abbreviation = models.CharField(
        max_length=8,
        unique=True,
       
    )
    description = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["abbreviation"]),
        ]



    def __str__(self):
        return self.name
