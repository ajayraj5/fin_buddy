# Copyright (c) 2025, AjayRaj Mahiwal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Client(Document):
    pass
    # def after_insert(self):
        
    #     frappe.get_doc({
    #         "doctype": "Income Tax Client",
    #         "client_id": self.name,
    #         "client_name": self.client_name,
    #         "dob": self.dob,
    #         "username": self.username,
    #         "password": self.password,
    #         "last_income_tax_sync": self.last_income_tax_sync
    #     }).insert()

    #     frappe.get_doc({
    #         "doctype": "GST Client",
    #         "client_id": self.name,
    #         "client_name": self.client_name,
    #         "gst_username": self.gst_username,
    #         "gst_password": self.gst_password,
    #         "last_gst_sync": self.last_gst_sync
    #     }).insert()

    #     frappe.get_doc({
    #         "doctype": "TDS Client",
    #         "client_id": self.name,
    #         "client_name": self.client_name,
    #         "tds_username": self.tds_username,
    #         "tds_password": self.tds_password,
    #         "last_tds_sync": self.last_tds_sync
    #     }).insert()

    # def validate(self):
    #     previous = self.get_doc_before_save()

    #     # frappe.log_error("password",self.password)
    #     if previous:
    #         # Update the Username and Password

    #         if self.disabled != previous.disabled or self.client_name != previous.client_name or self.dob != previous.dob or self.username != previous.username or self.password != previous.password:
    #             client = frappe.get_value("Income Tax Client", {'client_id': self.name}, "name")

    #             if client:
    #                 income_tax_client = frappe.get_doc("Income Tax Client", client)
    #                 income_tax_client.username = self.username
    #                 income_tax_client.set("password", self.password)
    #                 income_tax_client.dob = self.dob
    #                 income_tax_client.client_name = self.client_name


    #                 income_tax_client.save()
    #                 frappe.db.commit()


    #         if self.disabled != previous.disabled or self.client_name != previous.client_name or self.gst_username != previous.gst_username or self.gst_password != previous.gst_password:
    #             client = frappe.get_value("GST Client", {'client_id': self.name}, "name")

    #             if client:
    #                 gst_client = frappe.get_doc("GST Client", client)
    #                 gst_client.client_id = self.name
    #                 gst_client.gst_username = self.gst_username
    #                 gst_client.set("gst_password", self.gst_password)
    #                 gst_client.client_name = self.client_name


    #                 gst_client.save()
    #                 frappe.db.commit()

    #         if self.disabled != previous.disabled or self.client_name != previous.client_name or self.tds_username != previous.tds_username or self.tds_password != previous.tds_password:
    #             client = frappe.get_value("TDS Client", {'client_id': self.name}, "name")

    #             if client:
    #                 tds_client = frappe.get_doc("TDS Client", client)
    #                 tds_client.tds_username = self.tds_username
    #                 tds_client.set("tds_password", self.tds_password)
    #                 tds_client.client_name = self.client_name


    #                 tds_client.save()
    #                 frappe.db.commit()


    #         # Update Last Sync Time


    #         if self.last_income_tax_sync != previous.last_income_tax_sync:
    #             client = frappe.get_value("Income Tax Client", {'client_id': self.name}, "name")

    #             if client:
    #                 income_tax_client = frappe.get_doc("Income Tax Client", client)
    #                 income_tax_client.last_income_tax_sync = self.last_income_tax_sync

    #                 income_tax_client.save()
    #                 frappe.db.commit()


    #         if self.last_gst_sync != previous.last_gst_sync:
    #             client = frappe.get_value("GST Client", {'client_id': self.name}, "name")

    #             if client:
    #                 gst_client = frappe.get_doc("GST Client", client)
    #                 gst_client.last_gst_sync = self.last_gst_sync

    #                 gst_client.save()
    #                 frappe.db.commit()


    #         if self.last_tds_sync != previous.last_tds_sync:
    #             client = frappe.get_value("TDS Client", {'client_id': self.name}, "name")

    #             if client:
    #                 tds_client = frappe.get_doc("TDS Client", client)
    #                 tds_client.last_tds_sync = self.last_tds_sync

    #                 tds_client.save()
    #                 frappe.db.commit()


    # def on_trash(self):
    #     income_tax_client = frappe.get_value("Income Tax Client", {'client_id': self.name}, "name")
    #     frappe.delete_doc("Income Tax Client", income_tax_client, ignore_permissions=True)

    #     gst_client = frappe.get_value("GST Client", {'client_id': self.name}, "name")
    #     frappe.delete_doc("GST Client", gst_client, ignore_permissions=True)

    #     tds_client = frappe.get_value("TDS Client", {'client_id': self.name}, "name")
    #     frappe.delete_doc("TDS Client", tds_client, ignore_permissions=True)


    
    # def update_password(self, doctype_name):


    # def validate(self):
    #     # Handle syncing with all client-related doctypes
    #     self.sync_with_related_doctypes()
        
    # def sync_with_related_doctypes(self):
    #     # Define all related doctypes and their sync flags
    #     related_doctypes = [
    #         {
    #             "doctype": "Income Tax Client",
    #             "flag": "in_sync",
    #             "fields": {
    #                 "client_name": "client_name",
    #                 "dob": "dob",
    #                 "username": "username",
    #                 "password": "password"
    #             }
    #         },
    #         {
    #             "doctype": "TDS Client",
    #             "flag": "in_tds_sync",
    #             "fields": {
    #                 "client_name": "client_name",
    #                 "disabled": "disabled",
    #                 "tds_username": "tds_username",
    #                 "tds_password": "tds_password"
    #             }
    #         },
    #         {
    #             "doctype": "GST Client",
    #             "flag": "in_gst_sync",
    #             "fields": {
    #                 "client_name": "client_name",
    #                 "disabled": "disabled",
    #                 "gst_username": "gst_username",
    #                 "gst_password": "gst_password"
    #             }
    #         }
    #     ]
        
    #     # Process each related doctype
    #     for config in related_doctypes:
    #         if getattr(frappe.flags, config["flag"], False):
    #             continue  # Skip if already in a sync process
                
    #         self.sync_with_doctype(
    #             doctype=config["doctype"],
    #             fields=config["fields"],
    #             flag=config["flag"]
    #         )
        
    # def sync_with_doctype(self, doctype, fields, flag):
    #     # Check if there's a corresponding record
    #     related_docs = frappe.get_all(
    #         doctype, 
    #         filters={"client_id": self.name},
    #         fields=["name"]
    #     )
        
    #     if not related_docs:
    #         return  # No linked document found
            
    #     try:
    #         # Get the related document
    #         related_doc_name = related_docs[0].name
    #         related_doc = frappe.get_doc(doctype, related_doc_name)
            
    #         # Check for changes and update
    #         update_needed = False
    #         for client_field, related_field in fields.items():
    #             if hasattr(self, client_field) and hasattr(related_doc, related_field) and getattr(self, client_field) != getattr(related_doc, related_field):
    #                 setattr(related_doc, related_field, getattr(self, client_field))
    #                 update_needed = True
    #                 # frappe.msgprint(f"Updated {related_field} in {doctype}")
            
    #         # Save if changes were made
    #         if update_needed:
    #             setattr(frappe.flags, flag, True)  # Set flag to prevent recursive updates
    #             related_doc.flags.ignore_permissions = True
    #             related_doc.flags.ignore_validate = True
    #             related_doc.save()
    #             # frappe.msgprint(f"{doctype} for {self.client_name} updated successfully")
    #             setattr(frappe.flags, flag, False)  # Reset flag
                    
    #     except Exception as e:
    #         frappe.log_error(f"Failed to sync {doctype} document: {str(e)}", f"Client to {doctype} Sync Error")








    # def after_insert_old(self):
    #     # Check if we should create an IncomeTaxClient record
    #     if hasattr(self, 'username') and self.username and hasattr(self, 'password') and self.password:
    #         self.create_income_tax_client()
            
    #     # Check if we should create a GSTClient record
    #     if hasattr(self, 'gst_username') and self.gst_username and hasattr(self, 'gst_password') and self.gst_password:
    #         self.create_gst_client()
            
    #     # Check if we should create a TDSClient record
    #     if hasattr(self, 'tds_username') and self.tds_username and hasattr(self, 'tds_password') and self.tds_password:
    #         self.create_tds_client()

    # def create_income_tax_client(self):
    #     # Check if an IncomeTaxClient already exists for this client
    #     existing = frappe.get_all(
    #         "Income Tax Client", 
    #         filters={"client_id": self.name},
    #         fields=["name"]
    #     )
        
    #     if existing:
    #         return  # Already exists, no need to create
            
    #     try:
    #         # Create new IncomeTaxClient
    #         income_tax_client = frappe.new_doc("Income Tax Client")
    #         income_tax_client.client_id = self.name
    #         income_tax_client.client_name = self.client_name
            
    #         # Copy other relevant fields
    #         if hasattr(self, 'dob'):
    #             income_tax_client.dob = self.dob
    #         income_tax_client.username = self.username
    #         income_tax_client.password = self.password
            
    #         # Set flag to prevent recursive validation
    #         frappe.flags.in_sync = True
    #         income_tax_client.flags.ignore_validate = True
    #         income_tax_client.insert()
    #         frappe.flags.in_sync = False
            
    #         # frappe.msgprint(f"IncomeTaxClient created for {self.client_name}")
    #     except Exception as e:
    #         frappe.log_error(f"Failed to create IncomeTaxClient: {str(e)}", "Client Auto Creation Error")

    # def create_gst_client(self):
    #     # Check if a GSTClient already exists for this client
    #     existing = frappe.get_all(
    #         "GST Client", 
    #         filters={"client_id": self.name},
    #         fields=["name"]
    #     )
        
    #     if existing:
    #         return  # Already exists, no need to create
            
    #     try:
    #         # Create new GSTClient
    #         gst_client = frappe.new_doc("GST Client")
    #         gst_client.client_id = self.name
    #         gst_client.client_name = self.client_name
            
    #         # Copy other relevant fields
    #         if hasattr(self, 'disabled'):
    #             gst_client.disabled = self.disabled
    #         gst_client.gst_username = self.gst_username
    #         gst_client.gst_password = self.gst_password
            
    #         # Set flag to prevent recursive validation
    #         frappe.flags.in_gst_sync = True
    #         gst_client.flags.ignore_validate = True
    #         gst_client.insert()
    #         frappe.flags.in_gst_sync = False
            
    #         # frappe.msgprint(f"GSTClient created for {self.client_name}")
    #     except Exception as e:
    #         frappe.log_error(f"Failed to create GSTClient: {str(e)}", "Client Auto Creation Error")

    # def create_tds_client(self):
    #     # Check if a TDSClient already exists for this client
    #     existing = frappe.get_all(
    #         "TDS Client", 
    #         filters={"client_id": self.name},
    #         fields=["name"]
    #     )
        
    #     if existing:
    #         return  # Already exists, no need to create
            
    #     try:
    #         # Create new TDSClient
    #         tds_client = frappe.new_doc("TDS Client")
    #         tds_client.client_id = self.name
    #         tds_client.client_name = self.client_name
            
    #         # Copy other relevant fields
    #         if hasattr(self, 'disabled'):
    #             tds_client.disabled = self.disabled
    #         tds_client.tds_username = self.tds_username
    #         tds_client.tds_password = self.tds_password
            
    #         # Set flag to prevent recursive validation
    #         frappe.flags.in_tds_sync = True
    #         tds_client.flags.ignore_validate = True
    #         tds_client.insert()
    #         frappe.flags.in_tds_sync = False
            
    #         # frappe.msgprint(f"TDSClient created for {self.client_name}")
    #     except Exception as e:
    #         frappe.log_error(f"Failed to create TDSClient: {str(e)}", "Client Auto Creation Error")




    # def validate_old(self):
        # Check if there's a corresponding IncomeTaxClient record
    #     income_tax_clients = frappe.get_all(
    #         "Income Tax Client", 
    #         filters={"client_id": self.name},
    #         fields=["name"]
    #     )
        
    #     if not income_tax_clients:
    #         return  # No linked IncomeTaxClient found
            
    #     try:
    #         # Get the IncomeTaxClient document
    #         income_tax_client_name = income_tax_clients[0].name
    #         income_tax_doc = frappe.get_doc("Income Tax Client", income_tax_client_name)
            
    #         # Fields to sync (fields that exist in both doctypes with the same name)
    #         fields_to_sync = [
    #             "client_name",
    #             "dob",
    #             "username",
    #             "password",
    #             "last_income_tax_sync",
    #             # Add any other fields that should be synced
    #         ]
            
    #         # Check for changes and update the IncomeTaxClient document
    #         update_needed = False
    #         for field in fields_to_sync:
    #             if hasattr(self, field) and hasattr(income_tax_doc, field) and getattr(self, field) != getattr(income_tax_doc, field):
    #                 setattr(income_tax_doc, field, getattr(self, field))
    #                 update_needed = True
    #                 # frappe.msgprint(f"Updated {field} in IncomeTaxClient")
            
    #         # Save the IncomeTaxClient document if changes were made
    #         if update_needed:
    #             income_tax_doc.flags.ignore_permissions = True  # Optional: bypass permissions
    #             income_tax_doc.flags.ignore_validate = True  # To prevent infinite loop
    #             income_tax_doc.save()
    #             # frappe.msgprint(f"Income Tax Client for {self.client_name} updated successfully")
                
    #     except Exception as e:
    #         frappe.log_error(f"Failed to sync IncomeTaxClient document: {str(e)}", "Client Sync Error")




    #         # def validate(self):
    # # First handle syncing with IncomeTaxClient (from your previous code)
    # # ...
    
    #     # Now handle syncing with TDSClient
    #     if frappe.flags.in_tds_sync:
    #         return  # Skip if already in a TDS sync process
        
    #     # Check if there's a corresponding TDSClient record
    #     tds_clients = frappe.get_all(
    #         "TDS Client", 
    #         filters={"client_id": self.name},
    #         fields=["name"]
    #     )
        
    #     if tds_clients:
    #         try:
    #             # Get the TDSClient document
    #             tds_client_name = tds_clients[0].name
    #             tds_doc = frappe.get_doc("TDS Client", tds_client_name)
                
    #             # Fields to sync (mapped between the two doctypes)
    #             fields_to_sync = {
    #                 "client_name": "client_name",  # Map Client field name to TDSClient field name
    #                 "disabled": "disabled",
    #                 "tds_username": "tds_username",
    #                 "tds_password": "tds_password"
    #             }
                
    #             update_needed = False
    #             for client_field, tds_field in fields_to_sync.items():
    #                 if hasattr(self, client_field) and hasattr(tds_doc, tds_field) and getattr(self, client_field) != getattr(tds_doc, tds_field):
    #                     setattr(tds_doc, tds_field, getattr(self, client_field))
    #                     update_needed = True
    #                     # frappe.msgprint(f"Updated {tds_field} in TDSClient")
                
    #             if update_needed:
    #                 frappe.flags.in_tds_sync = True  # Set flag to prevent recursive updates
    #                 tds_doc.flags.ignore_permissions = True
    #                 tds_doc.flags.ignore_validate = True
    #                 tds_doc.save()
    #                 # frappe.msgprint(f"TDSClient for {self.client_name} updated successfully")
    #                 frappe.flags.in_tds_sync = False  # Reset flag
                    
    #         except Exception as e:
    #             frappe.log_error(f"Failed to sync TDSClient document: {str(e)}", "Client to TDS Sync Error")