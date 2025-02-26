// Copyright (c) 2025, AjayRaj Mahiwal and contributors
// For license information, please see license.txt

frappe.query_reports["GST Notice Summary"] = {
	"filters": [
		{
			"label": "GST Notice ID",
			"fieldname": "gst_notice_id",
			"fieldtype": "Link",
			"options": "GST Notice"
		},
		{
			"label": "Issue Date",
			"fieldname": "issue_date",
			"fieldtype": "Date",
		}
	]
};
