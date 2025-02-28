# Copyright (c) 2025, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}
    
    columns = get_columns()
    data = get_data(filters)
    
    return columns, data

def get_columns():
    return [
        {"label": _("Notice Type"), "fieldname": "notice_type", "fieldtype": "Data", "width": 150},
        {"label": _("Client ID"), "fieldname": "client", "fieldtype": "Link", "options": "Client", "width": 120},
        {"label": _("Client Name"), "fieldname": "client_name", "fieldtype": "Data", "width": 180},
        {"label": _("Document Reference"), "fieldname": "reference_id", "fieldtype": "Data", "width": 180},
        {"label": _("Document"), "fieldname": "document_link", "fieldtype": "HTML", "width": 100},
        {"label": _("Assessment Year"), "fieldname": "assessment_year", "fieldtype": "Data", "width": 120},
        {"label": _("Notice/Demand Date"), "fieldname": "notice_date", "fieldtype": "Date", "width": 120},
        {"label": _("Due Date"), "fieldname": "due_date", "fieldtype": "Date", "width": 120},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
        {"label": _("Amount"), "fieldname": "amount", "fieldtype": "Currency", "width": 120},
        {"label": _("Last Response Date"), "fieldname": "last_response_date", "fieldtype": "Date", "width": 120},
        {"label": _("Notice Letter"), "fieldname": "notice_letter_link", "fieldtype": "HTML", "width": 120},
        {"label": _("Response Acknowledgement"), "fieldname": "response_ack_link", "fieldtype": "HTML", "width": 150},
    ]

def get_data(filters):
    data = []
    
    # Get E Proceeding data
    if not filters.get("notice_type") or filters.get("notice_type") == "E Proceeding":
        e_proceeding_conditions = get_conditions(filters, "E Proceeding")
        e_proceeding_query = """
            SELECT 
                'E Proceeding' as notice_type,
                ep.name as doc_name,
                ep.client,
                cl.client_name,
                ep.notice_communication_reference_id as reference_id,
                ep.assessment_year,
                ep.proceeding_status as status,
                0 as amount,
                STR_TO_DATE(ep.last_response_submitted, '%%d-%%m-%%Y') as last_response_date,
                ep.notice_letter,
                ep.response_acknowledgement
            FROM 
                `tabE Proceeding` ep
            LEFT JOIN
                `tabClient` cl ON ep.client = cl.name
            WHERE 
                {conditions}
        """.format(conditions=e_proceeding_conditions)
        
		#   STR_TO_DATE(ep.notice_sent_date, '%%d-%%m-%%Y') as notice_date,
        # 	STR_TO_DATE(ep.response_due_date, '%%d-%%m-%%Y') as due_date,
        
        e_proceeding_data = frappe.db.sql(e_proceeding_query, filters, as_dict=1)
        
        for row in e_proceeding_data:
            row['document_link'] = f'<a href="/app/e-proceeding/{row.doc_name}" target="_blank">View</a>'
            row['notice_letter_link'] = get_attachment_link(row.notice_letter, "Notice")
            row['response_ack_link'] = get_attachment_link(row.response_acknowledgement, "Acknowledgement")
        
        data.extend(e_proceeding_data)
    
    # Get Response to Outstanding Demand data
    if not filters.get("notice_type") or filters.get("notice_type") == "Response to Outstanding Demand":
        rod_conditions = get_conditions(filters, "Response to Outstanding Demand")
        rod_query = """
            SELECT 
                'Response to Outstanding Demand' as notice_type,
                rod.name as doc_name,
                rod.client,
                cl.client_name,
                rod.demand_reference_no as reference_id,
                rod.assessment_year,
                NULL as notice_date,
                NULL as due_date,
                rod.response_type as status,
                CAST(rod.outstanding_demand_amount AS DECIMAL(18,2)) as amount,
                NULL as last_response_date,
                rod.notice as notice_doc
            FROM 
                `tabResponse to Outstanding Demand` rod
            LEFT JOIN
                `tabClient` cl ON rod.client = cl.name
            WHERE 
                {conditions}
        """.format(conditions=rod_conditions)
        
        rod_data = frappe.db.sql(rod_query, filters, as_dict=1)
        
        for row in rod_data:
            row['document_link'] = f'<a href="/app/response-to-outstanding-demand/{row.doc_name}" target="_blank">View</a>'
            row['notice_letter_link'] = get_attachment_link(row.notice_doc, "Notice")
            row['response_ack_link'] = ""
        
        data.extend(rod_data)
    
    return data


def get_document_link(doctype, name):
    return f'''<a href="/app/{frappe.scrub(doctype)}/{name}" target="_blank">View</a>'''


def get_attachment_link(file_url, label):
    if not file_url:
        return ""
    return f'''<a href="{file_url}" target="_blank">{label}</a>'''

def get_conditions(filters, doctype):
    conditions = ["1=1"]
    table_alias = "ep" if doctype == "E Proceeding" else "rod"
    
    if filters.get("client"):
        conditions.append(f"{table_alias}.client = %(client)s")
    
    if filters.get("assessment_year"):
        conditions.append(f"{table_alias}.assessment_year = %(assessment_year)s")
    
    if filters.get("from_date") and doctype == "E Proceeding":
        conditions.append(f"STR_TO_DATE({table_alias}.notice_sent_date, '%%d-%%m-%%Y') >= %(from_date)s")
    
    if filters.get("to_date") and doctype == "E Proceeding":
        conditions.append(f"STR_TO_DATE({table_alias}.notice_sent_date, '%%d-%%m-%%Y') <= %(to_date)s")
    
    return " AND ".join(conditions)