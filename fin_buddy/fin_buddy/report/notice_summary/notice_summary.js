// Copyright (c) 2025, AjayRaj Mahiwal and contributors
// For license information, please see license.txt

frappe.query_reports["Notice Summary"] = {
    "filters": [
        {
            "fieldname": "client",
            "label": __("Client"),
            "fieldtype": "Link",
            "options": "Client",
            "mandatory": 0
        },
        {
            "fieldname": "notice_type",
            "label": __("Notice Type"),
            "fieldtype": "Select",
            "options": "\nE Proceeding\nResponse to Outstanding Demand",
            "mandatory": 0
        },
        {
            "fieldname": "assessment_year",
            "label": __("Assessment Year"),
            "fieldtype": "Data",
            "mandatory": 0
        },
        // {
        //     "fieldname": "from_date",
        //     "label": __("From Date"),
        //     "fieldtype": "Date",
        //     "mandatory": 0,
        //     "default": frappe.datetime.add_months(frappe.datetime.get_today(), -3)
        // },
        // {
        //     "fieldname": "to_date",
        //     "label": __("To Date"),
        //     "fieldtype": "Date",
        //     "mandatory": 0,
        //     "default": frappe.datetime.get_today()
        // }
    ],
    
    "formatter": function(value, row, column, data, default_formatter) {
        value = default_formatter(value, row, column, data);
        
        if (column.fieldname == "status") {
            if (data.notice_type == "E Proceeding") {
                if (value == "Completed") {
                    value = "<span style='color:green'>" + value + "</span>";
                } else if (value == "Pending") {
                    value = "<span style='color:red'>" + value + "</span>";
                } else if (value == "In Progress") {
                    value = "<span style='color:orange'>" + value + "</span>";
                }
            }
        }
        
        return value;
    },
    
    "onload": function(report) {
        report.page.add_inner_button(__('Export Selected'), function() {
            const selected_rows = report.datatable.rowmanager.getCheckedRows();
            if (selected_rows.length === 0) {
                frappe.msgprint(__("No rows selected"));
                return;
            }
            
            const indices = selected_rows.map(row => row.meta.rowIndex);
            const selected_data = indices.map(i => report.data[i]);
            
            frappe.tools.downloadify(selected_data, null, "Notice_Summary_Selected");
        });
    }
};