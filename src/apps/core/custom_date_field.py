from rest_framework import serializers
from datetime import datetime


class CustomDateField(serializers.DateField):
    def to_internal_value(self, value):
        try:
            # Convert from dd-mm-yyyy to yyyy-mm-dd
            parsed_date = datetime.strptime(value, "%d-%m-%Y").date()
        except ValueError:
            raise serializers.ValidationError("Date format should be dd-mm-yyyy")
        return parsed_date

    def to_representation(self, value):
        # Convert from yyyy-mm-dd to dd-mm-yyyy
        return value.strftime("%d-%m-%Y")
