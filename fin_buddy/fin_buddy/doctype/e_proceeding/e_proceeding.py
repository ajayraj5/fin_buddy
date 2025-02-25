# Copyright (c) 2025, AjayRaj Mahiwal and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from pathlib import Path
from frappe.model.document import Document


class EProceeding(Document):
	def validate(self):
		validate_other_documents_format(self)





def validate_other_documents_format(doc):
    """
    Simple validation for files in the other_document child table of E Proceeding doctype.
    """
    # List of allowed file extensions
    allowed_extensions = ['.pdf', '.doc', '.docx']
    
    # Check each row in other_document table
    for row in doc.other_documents:
        if not row.file:
            frappe.throw(
                _("Please attach a file in row {0} of Other Documents").format(row.idx)
            )
        
        # Check file extension
        file_extension = Path(row.file).suffix.lower()
        if file_extension not in allowed_extensions:
            frappe.throw(
                _("Invalid file format in row {0}. Only PDF, DOC, and DOCX files are allowed").format(row.idx)
            )
