"""Crypto Correctness Tests per TESTING.md Section 1

Verifies:
1. Round-trip test: decrypt(encrypt(plaintext)) == plaintext for various inputs
2. Wrong-key test: decrypting with incorrect key raises clear exception
3. Tamper test: flipping a byte fails decryption (proves HMAC integrity)
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared import crypto_utils


class TestCryptoUtils(unittest.TestCase):
    def setUp(self):
        self.key1 = crypto_utils.generate_key()
        self.key2 = crypto_utils.generate_key()

    def test_round_trip_variations(self):
        """Test round-trip encryption for empty, short, long, and unicode strings."""
        test_cases = [
            "",  # Empty string
            "Hello, World!",  # Standard string
            "CONFIDENTIAL: Project-Titan-Alpha acquisition finalized at $14.25M.",
            "Special characters: !@#$%^&*()_+{}[]:;'\"<>,.?/|\\~`",
            "Unicode test: 🚀 🔐 🛡️ 漢字 日本語 العربية Русский €£¥",
            "A" * 10000,  # Long string (10 KB)
        ]

        for original in test_cases:
            ciphertext = crypto_utils.encrypt(original, key=self.key1)
            self.assertIsInstance(ciphertext, str)
            self.assertNotEqual(ciphertext, original)
            decrypted = crypto_utils.decrypt(ciphertext, key=self.key1)
            self.assertEqual(decrypted, original, f"Failed round-trip for input: {original[:30]}...")

    def test_wrong_key_fails(self):
        """Test that decrypting with wrong key raises DecryptionError, never returning garbage."""
        plaintext = "TOP SECRET: Acquisition terms"
        ciphertext = crypto_utils.encrypt(plaintext, key=self.key1)

        with self.assertRaises(crypto_utils.DecryptionError):
            crypto_utils.decrypt(ciphertext, key=self.key2)

    def test_tamper_detection(self):
        """Test that modifying even a single byte of ciphertext causes HMAC validation to fail."""
        plaintext = "Project-Titan-Alpha acquisition details"
        ciphertext = crypto_utils.encrypt(plaintext, key=self.key1)

        # Tamper with one character in the middle of the base64 ciphertext
        tampered_chars = list(ciphertext)
        idx_to_flip = len(tampered_chars) // 2
        tampered_chars[idx_to_flip] = "A" if tampered_chars[idx_to_flip] != "A" else "B"
        tampered_ciphertext = "".join(tampered_chars)

        with self.assertRaises(crypto_utils.DecryptionError):
            crypto_utils.decrypt(tampered_ciphertext, key=self.key1)


if __name__ == "__main__":
    unittest.main()
