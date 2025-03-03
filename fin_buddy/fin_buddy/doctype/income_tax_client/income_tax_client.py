# Copyright (c) 2025, AjayRaj Mahiwal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class IncomeTaxClient(Document):
    pass
		# def validate(self):
		# 	if self.client_id:
		# 		# Get the Client document that is linked
		# 		client_doc = frappe.get_doc("Client", self.client_id)
				
		# 		# Fields to sync (fields that exist in both doctypes with the same name)
		# 		fields_to_sync = [
		# 			"dob",
		# 			"username",
		# 			"password",
		# 			"last_income_tax_sync"
		# 			# Add any other fields that should be synced
		# 		]
				
		# 		# Check for changes and update the Client document
		# 		update_needed = False
		# 		for field in fields_to_sync:
		# 			if hasattr(self, field) and getattr(self, field) != getattr(client_doc, field):
		# 				setattr(client_doc, field, getattr(self, field))
		# 				update_needed = True
				
		# 		# Save the Client document if changes were made
		# 		if update_needed:
		# 			client_doc.save()
	# def validate(self):
	# 	if not self.client_id or frappe.flags.in_sync:
	# 		return
			
	# 	frappe.flags.in_sync = True  # Set a flag to prevent recursive syncing
		
	# 	try:
	# 		client_doc = frappe.get_doc("Client", self.client_id)
			
	# 		fields_to_sync = [
	# 			"client_name",
	# 			"dob",
	# 			"username",
	# 			"password",
	# 			"last_income_tax_sync"
	# 		]
			
	# 		update_needed = False
	# 		for field in fields_to_sync:
	# 			if hasattr(self, field) and hasattr(client_doc, field) and getattr(self, field) != getattr(client_doc, field):
	# 				setattr(client_doc, field, getattr(self, field))
	# 				update_needed = True
			
	# 		if update_needed:
	# 			client_doc.flags.ignore_permissions = True
	# 			client_doc.flags.ignore_validate = True  # To prevent infinite loop
	# 			client_doc.save()
				
	# 	except Exception as e:
	# 		frappe.log_error(f"Failed to sync Client document: {str(e)}", "IncomeTaxClient Sync Error")
	# 	finally:
	# 		frappe.flags.in_sync = False  # Reset the flag