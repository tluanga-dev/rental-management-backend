from django.test import TestCase

from config import settings
from .models import IdManager
from django.core.exceptions import ValidationError
import threading


class IdManagerTest(TestCase):
    def setUp(self):
        # Clear existing entries before each test
        IdManager.objects.all().delete()

    def test_initial_id_generation(self):
        """Test first ID creation for a new prefix"""
        id1 = IdManager.generate_id("PUR")
        self.assertEqual(id1, "PUR-AAA0001")

        id2 = IdManager.generate_id("SAL")
        self.assertEqual(id2, "SAL-AAA0001")

    def test_sequential_number_increment(self):
        """Test basic number increment within same letter sequence"""
        ids = [IdManager.generate_id("TEST") for _ in range(5)]
        expected = [
            "TEST-AAA0001",
            "TEST-AAA0002",
            "TEST-AAA0003",
            "TEST-AAA0004",
            "TEST-AAA0005",
        ]
        self.assertEqual(ids, expected)

    def test_letter_increment_after_number_overflow(self):
        """Test letter sequence increments when numbers reach max"""
        # Set initial state to just before overflow
        IdManager.objects.create(prefix="TEST", latest_id="TEST-AAA9999")

        new_id = IdManager.generate_id("TEST")
        self.assertEqual(new_id, "TEST-AAB0001")

    def test_full_letter_sequence_overflow(self):
        """Test letter sequence carry-over (ZZZ -> AAAA)"""
        IdManager.objects.create(prefix="TEST", latest_id="TEST-ZZZ9999")

        new_id = IdManager.generate_id("TEST")
        self.assertEqual(new_id, "TEST-AAAA0001")

    def test_invalid_id_format_recovery(self):
        """Test automatic reset on corrupted ID format"""
        IdManager.objects.create(prefix="CORRUPT", latest_id="CORRUPT-bad_id_123")

        new_id = IdManager.generate_id("CORRUPT")
        self.assertEqual(new_id, "CORRUPT-AAA0001")

    def test_concurrent_id_generation(self):
        """Test thread-safe ID generation under concurrency"""
        if "sqlite" in settings.DATABASES["default"]["ENGINE"]:
            self.skipTest("Skipping concurrency test for SQLite")

        results = []
        threads = []
        thread_count = 5
        ids_per_thread = 10

        def generate_ids():
            try:
                ids = [IdManager.generate_id("CONC") for _ in range(ids_per_thread)]
                results.extend(ids)
            except Exception as e:
                self.fail(f"ID generation failed: {str(e)}")

        # Create and start threads
        for _ in range(thread_count):
            t = threading.Thread(target=generate_ids)
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        # Verify all IDs are unique
        self.assertEqual(len(results), len(set(results)), "Duplicate IDs generated")

        # Extract and verify numeric sequence
        numbers = []
        for id in results:
            prefix, sequence = id.split("-")
            # Verify prefix matches
            self.assertEqual(prefix, "CONC", "Invalid prefix in generated ID")
            # Extract numeric part
            num_part = "".join(filter(str.isdigit, sequence))
            numbers.append(int(num_part))

        # Verify numbers are sequential and cover expected range
        numbers.sort()
        expected_numbers = list(range(1, thread_count * ids_per_thread + 1))
        self.assertEqual(
            numbers, expected_numbers, "ID sequence contains gaps or duplicates"
        )

    def test_single_letter_sequence(self):
        """Test increment with single-letter sequences"""
        IdManager.objects.create(prefix="SL", latest_id="SL-A9999")

        new_id = IdManager.generate_id("SL")
        self.assertEqual(new_id, "SL-B0001")

    def test_empty_letter_sequence(self):
        """Test handling of IDs with no letters"""
        IdManager.objects.create(prefix="NL", latest_id="NL-9999")

        new_id = IdManager.generate_id("NL")
        self.assertEqual(new_id, "NL-AAA0001")

    def test_increment_letters_helper(self):
        """Test letter increment logic directly"""
        self.assertEqual(IdManager._increment_letters("A"), "B")
        self.assertEqual(IdManager._increment_letters("Z"), "AA")
        self.assertEqual(IdManager._increment_letters("AZ"), "BA")
        self.assertEqual(IdManager._increment_letters("ZZ"), "AAA")
        self.assertEqual(IdManager._increment_letters(""), "A")

    def test_increment_id_validation(self):
        """Test validation of bad ID formats"""
        with self.assertRaises(ValidationError):
            IdManager._increment_id("BAD-ID", "BAD")

        with self.assertRaises(ValidationError):
            IdManager._increment_id("TEST-1234", "TEST")

        with self.assertRaises(ValidationError):
            IdManager._increment_id("TEST-AAA0000X", "TEST")

    def test_long_prefix_handling(self):
        """Test prefixes longer than 3 characters"""
        long_prefix = "LONG-PREFIX"
        id1 = IdManager.generate_id(long_prefix)
        self.assertEqual(id1, f"{long_prefix}-AAA0001")

    def test_case_insensitive_handling(self):
        """Test mixed case handling in existing IDs"""
        IdManager.objects.create(prefix="MIXED", latest_id="MIXED-AaB1234")

        new_id = IdManager.generate_id("MIXED")
        self.assertEqual(new_id, "MIXED-AAB1235")
