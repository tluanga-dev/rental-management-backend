# contact/models.py
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class ContactNumber(models.Model):
    number = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r"^\+?1?\d{9,15}$", message="Enter a valid phone number."
            )
        ],
    )

    # Generic Foreign Key (now allowing multiple entries per instance)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()  # Matches your UUID primary key
    content_object = GenericForeignKey("content_type", "object_id")

    constraints = [
        # Enforce unique number per instance (content_type + object_id + number)
        models.UniqueConstraint(
            fields=["content_type", "object_id", "number"],
            name="unique_contact_per_instance",
        )
    ]

    def __str__(self):
        return self.number
