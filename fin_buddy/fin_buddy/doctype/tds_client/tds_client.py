# Copyright (c) 2025, AjayRaj Mahiwal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TDSClient(Document):
    pass
	# def validate(self):
	# 	if not self.client_id or frappe.flags.in_tds_sync:
	# 		return
			
	# 	frappe.flags.in_tds_sync = True  # Set a flag to prevent recursive syncing
		
	# 	try:
	# 		client_doc = frappe.get_doc("Client", self.client_id)
			
	# 		# Fields to sync (fields that exist in both doctypes)
	# 		fields_to_sync = {
	# 			"client_name": "client_name",
	# 			"disabled": "disabled",
	# 			"tds_username": "tds_username",  # Map TDSClient field name to Client field name
	# 			"tds_password": "tds_password"   # Map TDSClient field name to Client field name
	# 		}
			
	# 		update_needed = False
	# 		for tds_field, client_field in fields_to_sync.items():
	# 			if hasattr(self, tds_field) and hasattr(client_doc, client_field) and getattr(self, tds_field) != getattr(client_doc, client_field):
	# 				setattr(client_doc, client_field, getattr(self, tds_field))
	# 				update_needed = True
			
	# 		if update_needed:
	# 			client_doc.flags.ignore_permissions = True
	# 			client_doc.flags.ignore_validate = True  # To prevent infinite loop
	# 			client_doc.save()
				
	# 	except Exception as e:
	# 		frappe.log_error(f"Failed to sync Client document: {str(e)}", "TDSClient Sync Error")
	# 	finally:
	# 		frappe.flags.in_tds_sync = False  # Reset the flag
