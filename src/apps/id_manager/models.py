import re
from django.db import models, transaction
from django.core.exceptions import ValidationError

from apps.base.time_stamped_abstract_class import TimeStampedAbstractModelClass


class IdManager(TimeStampedAbstractModelClass):
    """
    Manages unique ID generation with format: PREFIX-ABC0001
    Where:
    - ABC: Incrementing letters (AAA, AAB, ..., ZZZ, AAAA)
    - 0001: Incrementing numbers (0001-9999)
    """

    PREFIX_LENGTH = 3  # Standard length for prefix codes
    DEFAULT_LETTERS = "AAA"  # Starting letters for new sequences
    DEFAULT_NUMBERS = "0001"  # Starting numbers for new sequences

    prefix = models.CharField(
        max_length=255, unique=True
    )  # Stores prefix codes (e.g., 'PUR', 'SAL')
    latest_id = models.TextField()  # Stores last generated ID for each prefix

    @classmethod
    def generate_id(cls, prefix):
        """
        Atomically generates the next ID in sequence for a given prefix
        Usage example: IdManager.generate_id('PUR') -> 'PUR-AAA0001'
        """
        with transaction.atomic():  # Start database transaction
            # Lock the row to prevent concurrent updates (critical for consistency)
            id_manager, created = cls.objects.select_for_update().get_or_create(
                prefix=prefix,
                defaults={
                    "latest_id": f"{prefix}-{cls.DEFAULT_LETTERS}{cls.DEFAULT_NUMBERS}"
                },
            )

            if not created:
                try:
                    # Increment the existing ID safely
                    next_id = cls._increment_id(id_manager.latest_id, prefix)
                except ValidationError:
                    # Reset to default format if corrupted ID detected
                    next_id = f"{prefix}-{cls.DEFAULT_LETTERS}{cls.DEFAULT_NUMBERS}"

                # Update and save the new ID
                id_manager.latest_id = next_id
                id_manager.save()

            return id_manager.latest_id

    @classmethod
    def _increment_id(cls, last_id, expected_prefix):
        """
        Internal method to increment ID components with case insensitivity
        Validates format: [prefix]-[letters][numbers]
        """
        # Validate ID structure using regex
        if not re.match(rf"^{re.escape(expected_prefix)}-[A-Za-z]+\d+$", last_id):
            raise ValidationError(f"Invalid ID format: {last_id}")

        # Split into prefix and sequence parts
        prefix_part, sequence_part = last_id.split("-", 1)
        match = re.match(r"^([A-Za-z]*)(\d+)$", sequence_part)

        # Extract and normalize letter case to uppercase
        letters = (match.group(1) or cls.DEFAULT_LETTERS).upper()  # Key fix here
        numbers = match.group(2)
        num_length = len(numbers)

        try:  # Convert numeric part safely
            num = int(numbers)
        except ValueError:
            raise ValidationError(f"Invalid numeric sequence: {numbers}")

        if num < (10**num_length - 1):
            # Increment number without changing letter sequence
            return f"{prefix_part}-{letters}{num + 1:0{num_length}d}"

        # Handle number overflow - increment letters and reset numbers
        new_letters = cls._increment_letters(letters)
        return f"{prefix_part}-{new_letters}{cls.DEFAULT_NUMBERS}"

    @staticmethod
    def _increment_letters(letters):
        """
        Increments letter sequence using right-to-left carryover
        Examples:
        'A' -> 'B'
        'Z' -> 'AA'
        'AZ' -> 'BA'
        'ZZZ' -> 'AAAA'
        """
        if not letters:  # Handle empty case
            return "A"

        chars = list(letters.upper())
        # Iterate from right to left
        for i in reversed(range(len(chars))):
            if chars[i] != "Z":
                chars[i] = chr(ord(chars[i]) + 1)  # Increment character
                return "".join(chars)
            chars[i] = "A"  # Reset to A and carry over

        # All characters were Z - add new character
        return "A" * (len(chars) + 1)
    
    @classmethod
    def health_check(cls):
        """
        Health check method to verify ID Manager service is operational.
        Returns a dictionary with status and diagnostic information.
        """
        try:
            # Try to access the database
            count = cls.objects.count()
            
            # Try to generate a test ID
            test_prefix = "_HEALTH_CHECK_"
            test_id = cls.generate_id(test_prefix)
            
            # Clean up test entry
            cls.objects.filter(prefix=test_prefix).delete()
            
            return {
                'status': 'healthy',
                'message': 'ID Manager service is operational',
                'prefix_count': count,
                'test_id_generated': test_id,
                'timestamp': models.functions.Now()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'ID Manager service error: {str(e)}',
                'error_type': type(e).__name__,
                'timestamp': models.functions.Now()
            }


# Example Usage 1: Basic ID Generation
# print(IdManager.generate_id('PUR'))  # First call: 'PUR-AAA0001'
# print(IdManager.generate_id('PUR'))  # Next call:  'PUR-AAA0002'

# # Example Usage 2: Sequence Overflow Handling
# # Simulate high-number ID
# manager = IdManager.objects.create(prefix='TEST', latest_id='TEST-ZZZ9999')
# print(IdManager.generate_id('TEST'))  # Returns 'TEST-AAAA0001'

# # Example Usage 3: Concurrent Safe Generation
# # Safe to use across multiple threads/workers due to:
# # 1. Database-level row locking (select_for_update)
# # 2. Atomic transactions
# # 3. Sequence management in persistent storage

# # Example Usage 4: Automatic Format Correction
# # If corrupted ID exists:
# corrupted = IdManager.objects.create(prefix='BAD', latest_id='BAD-invalidID')
# print(IdManager.generate_id('BAD'))  # Returns 'BAD-AAA0001' (auto-reset)
