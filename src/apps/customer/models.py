from django.db import models
from django.core.validators import RegexValidator, MaxLengthValidator
from django.contrib.contenttypes.fields import GenericRelation

from apps.core.apps.contact_number.models import ContactNumber
from apps.base.time_stamped_abstract_class import TimeStampedAbstractModelClass


class Customer(TimeStampedAbstractModelClass):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    remarks = models.CharField(
        max_length=255, blank=True, null=True
    )  # Changed to CharField
    city = models.CharField(max_length=255, blank=True, null=True)
    # Reverse relation for contact numbers
    contact_numbers = GenericRelation(
        ContactNumber,
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="customer",
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name
