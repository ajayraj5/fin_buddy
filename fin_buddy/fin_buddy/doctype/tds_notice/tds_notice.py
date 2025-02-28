# Copyright (c) 2025, AjayRaj Mahiwal and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TDSNotice(Document):
    def on_trash(self):
        summary_detail_ids = [row.tds_summary_details for row in self.notices]

        frappe.db.delete("TDS Notice Item", {"parent": self.name})

        for summary_id in summary_detail_ids:
            frappe.delete_doc("TDS Summary Details", summary_id, ignore_permissions=True)

        
        summary_detail_list = frappe.get_all("TDS Summary Details", filters={'tds_notice': self.name})

        for summary in summary_detail_list:
            frappe.delete_doc("TDS Summary Details", summary.name, ignore_permissions=True)
