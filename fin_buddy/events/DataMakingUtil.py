import re
from datetime import datetime
import json
from typing import Dict, Tuple, List
import uuid


class DataMaskingUtil:
    def __init__(self):
        # Store original to masked mappings
        self.mapping = {}

        # Regex patterns for different data types
        self.patterns = {
            "pan": r"[A-Z]{5}[0-9]{4}[A-Z]{1}",
            "din": r"ITBA/[\w/.-]+",
            "dates": r"\d{2}/\d{2}/\d{4}|\d{2}-\d{2}-\d{4}",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "amount": r"(?:Rs\.?\s*)?\d+(?:,\d+)*(?:\.\d{2})?",
        }

        # Initialize counters for different types of placeholders
        self.counters = {
            "ENTITY": 1,
            "PAN": 1,
            "DIN": 1,
            "DATE": 1,
            "EMAIL": 1,
            "ADDRESS": 1,
        }

    def generate_placeholder(self, type_name: str) -> str:
        """Generate a unique placeholder for a given type"""
        placeholder = f"<<{type_name}_{self.counters[type_name]}>>"
        self.counters[type_name] += 1
        return placeholder

    def mask_dates(self, text: str) -> str:
        """Mask dates in the text"""

        def replace_date(match):
            date_str = match.group(0)
            placeholder = self.generate_placeholder("DATE")
            self.mapping[placeholder] = date_str
            return placeholder

        return re.sub(self.patterns["dates"], replace_date, text)

    def mask_pan(self, text: str) -> str:
        """Mask PAN numbers"""

        def replace_pan(match):
            pan = match.group(0)
            placeholder = self.generate_placeholder("PAN")
            self.mapping[placeholder] = pan
            return placeholder

        return re.sub(self.patterns["pan"], replace_pan, text)

    def mask_entities(self, text: str, entities: List[str]) -> str:
        """Mask specific entity names"""
        for entity in entities:
            if entity in text:
                placeholder = self.generate_placeholder("ENTITY")
                self.mapping[placeholder] = entity
                text = text.replace(entity, placeholder)
        return text

    def mask_din(self, text: str) -> str:
        """Mask DIN numbers"""

        def replace_din(match):
            din = match.group(0)
            placeholder = self.generate_placeholder("DIN")
            self.mapping[placeholder] = din
            return placeholder

        return re.sub(self.patterns["din"], replace_din, text)

    def mask_email(self, text: str) -> str:
        """Mask email addresses"""

        def replace_email(match):
            email = match.group(0)
            placeholder = self.generate_placeholder("EMAIL")
            self.mapping[placeholder] = email
            return placeholder

        return re.sub(self.patterns["email"], replace_email, text)

    def mask_text(self, text: str, entities_to_mask: List[str] = None) -> str:
        """
        Main method to mask all sensitive information in text
        Returns masked text and stores mapping internally
        """
        masked_text = text

        # Mask specific entities first if provided
        if entities_to_mask:
            masked_text = self.mask_entities(masked_text, entities_to_mask)

        # Apply all other masks
        masked_text = self.mask_pan(masked_text)
        masked_text = self.mask_din(masked_text)
        masked_text = self.mask_dates(masked_text)
        masked_text = self.mask_email(masked_text)

        return masked_text

    def restore_text(self, masked_text: str) -> str:
        """
        Restore original values from masked text using stored mapping
        """
        restored_text = masked_text

        # Sort mappings by length of placeholder (longest first)
        # This prevents partial replacements of similar placeholders
        sorted_mappings = sorted(
            self.mapping.items(),
            key=lambda x: len(x[0]),
            reverse=True,
        )

        # Replace each placeholder with its original value
        for placeholder, original in sorted_mappings:
            restored_text = restored_text.replace(placeholder, original)

        return restored_text

    def save_mapping(self, filename: str):
        """Save the current mapping to a file"""
        with open(filename, "w") as f:
            json.dump(self.mapping, f, indent=2)

    def load_mapping(self, filename: str):
        """Load mapping from a file"""
        with open(filename, "r") as f:
            self.mapping = json.load(f)
