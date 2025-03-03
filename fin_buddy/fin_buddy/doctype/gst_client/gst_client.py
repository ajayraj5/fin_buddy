# Copyright (c) 2025, AjayRaj Mahiwal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class GSTClient(Document):
    pass
	# def validate(self):
	# 	if not self.client_id or frappe.flags.in_gst_sync:
	# 		return
			
	# 	frappe.flags.in_gst_sync = True  # Set a flag to prevent recursive syncing
		
	# 	try:
	# 		client_doc = frappe.get_doc("Client", self.client_id)
			
	# 		# Fields to sync (fields that exist in both doctypes)
	# 		fields_to_sync = {
	# 			"client_name": "client_name",
	# 			"disabled": "disabled",
	# 			"gst_username": "gst_username",  # Map GSTClient field name to Client field name
	# 			"gst_password": "gst_password"   # Map GSTClient field name to Client field name
	# 		}
			
	# 		update_needed = False
	# 		for gst_field, client_field in fields_to_sync.items():
	# 			if hasattr(self, gst_field) and hasattr(client_doc, client_field) and getattr(self, gst_field) != getattr(client_doc, client_field):
	# 				setattr(client_doc, client_field, getattr(self, gst_field))
	# 				update_needed = True
	# 				# frappe.msgprint(f"Updated {client_field} in Client")
			
	# 		if update_needed:
	# 			client_doc.flags.ignore_permissions = True
	# 			client_doc.flags.ignore_validate = True  # To prevent infinite loop
	# 			client_doc.save()
	# 			# frappe.msgprint(f"Client {self.client_name} updated successfully from GST Client")
				
	# 	except Exception as e:
	# 		frappe.log_error(f"Failed to sync Client document: {str(e)}", "GSTClient Sync Error")
	# 	finally:
	# 		frappe.flags.in_gst_sync = False  # Reset the flag
