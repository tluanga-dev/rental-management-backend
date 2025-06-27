from django.db import models
from django.core.validators import RegexValidator
from django.contrib.contenttypes.fields import GenericRelation

# Correct the import path for ContactNumber
from apps.core.apps.contact_number.models import ContactNumber
from apps.base.time_stamped_abstract_class import TimeStampedAbstractModelClass

# class ContactNumber(models.Model):
#     number = models.CharField(
#         max_length=20,
#         validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Enter a valid phone number.")]
#     )
#     vendor = models.ForeignKey('Vendor', related_name='contact_numbers', on_delete=models.CASCADE)

#     def __str__(self):
#         return self.number


class Vendor(TimeStampedAbstractModelClass):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    remarks = models.TextField(max_length=255, blank=True, null=True)
    city = models.TextField(max_length=255, blank=True, null=True)
    # Reverse relation for contact numbers
    contact_numbers = GenericRelation(
        ContactNumber,
        content_type_field="content_type",
        object_id_field="object_id",
        related_query_name="vendor",
    )

    def delete(self, *args, **kwargs):
        # Delete all associated contact numbers before deleting the vendor
        self.contact_numbers.all().delete()
        super().delete(*args, **kwargs)

    def __str__(self):
        return self.name
