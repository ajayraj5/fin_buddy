# Copyright (c) 2025, AjayRaj Mahiwal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Client(Document):
    def after_insert(self):
        
        frappe.get_doc({
            "doctype": "Income Tax Client",
            "client_id": self.name,
            "username": self.username,
            "password": self.password,
            "last_income_tax_sync": self.last_income_tax_sync
        }).insert()

        frappe.get_doc({
            "doctype": "GST Client",
            "client_id": self.name,
            "gst_username": self.gst_username,
            "gst_password": self.gst_password,
            "last_gst_sync": self.last_gst_sync
        }).insert()

        frappe.get_doc({
            "doctype": "TDS Client",
            "client_id": self.name,
            "tds_username": self.tds_username,
            "tds_password": self.tds_password,
            "last_tds_sync": self.last_tds_sync
        }).insert()

    def validate(self):
        previous = self.get_doc_before_save()

        # frappe.log_error("password",self.password)
        if previous:
            # Update the Username and Password

            if self.disabled != previous.disabled or self.client_name != previous.client_name or self.dob != previous.dob or self.username != previous.username or self.password != previous.password:
                client = frappe.get_value("Income Tax Client", {'client_id': self.name}, "name")

                if client:
                    income_tax_client = frappe.get_doc("Income Tax Client", client)
                    income_tax_client.username = self.username
                    income_tax_client.set("password", self.password)
                    income_tax_client.dob = self.dob
                    income_tax_client.client_name = self.client_name


                    income_tax_client.save()
                    frappe.db.commit()


            if self.disabled != previous.disabled or self.client_name != previous.client_name or self.gst_username != previous.gst_username or self.gst_password != previous.gst_password:
                client = frappe.get_value("GST Client", {'client_id': self.name}, "name")

                if client:
                    gst_client = frappe.get_doc("GST Client", client)
                    gst_client.client_id = self.name
                    gst_client.gst_username = self.gst_username
                    gst_client.set("gst_password", self.gst_password)
                    gst_client.client_name = self.client_name


                    gst_client.save()
                    frappe.db.commit()

            if self.disabled != previous.disabled or self.client_name != previous.client_name or self.tds_username != previous.tds_username or self.tds_password != previous.tds_password:
                client = frappe.get_value("TDS Client", {'client_id': self.name}, "name")

                if client:
                    tds_client = frappe.get_doc("TDS Client", client)
                    tds_client.tds_username = self.tds_username
                    tds_client.set("tds_password", self.tds_password)
                    tds_client.client_name = self.client_name


                    tds_client.save()
                    frappe.db.commit()


            # Update Last Sync Time


            if self.last_income_tax_sync != previous.last_income_tax_sync:
                client = frappe.get_value("Income Tax Client", {'client_id': self.name}, "name")

                if client:
                    income_tax_client = frappe.get_doc("Income Tax Client", client)
                    income_tax_client.last_income_tax_sync = self.last_income_tax_sync

                    income_tax_client.save()
                    frappe.db.commit()


            if self.last_gst_sync != previous.last_gst_sync:
                client = frappe.get_value("GST Client", {'client_id': self.name}, "name")

                if client:
                    gst_client = frappe.get_doc("GST Client", client)
                    gst_client.last_gst_sync = self.last_gst_sync

                    gst_client.save()
                    frappe.db.commit()


            if self.last_tds_sync != previous.last_tds_sync:
                client = frappe.get_value("TDS Client", {'client_id': self.name}, "name")

                if client:
                    tds_client = frappe.get_doc("TDS Client", client)
                    tds_client.last_tds_sync = self.last_tds_sync

                    tds_client.save()
                    frappe.db.commit()


    def on_trash(self):
        income_tax_client = frappe.get_value("Income Tax Client", {'client_id': self.name}, "name")
        frappe.delete_doc("Income Tax Client", income_tax_client, ignore_permissions=True)

        gst_client = frappe.get_value("GST Client", {'client_id': self.name}, "name")
        frappe.delete_doc("GST Client", gst_client, ignore_permissions=True)

        tds_client = frappe.get_value("TDS Client", {'client_id': self.name}, "name")
        frappe.delete_doc("TDS Client", tds_client, ignore_permissions=True)



    # def update_password(self, doctype_name):