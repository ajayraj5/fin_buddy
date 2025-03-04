import frappe
import wrapt
from bs4 import BeautifulSoup
from frappe.query_builder import Order


def gen_response(status, message, data=[]):
    frappe.response["http_status_code"] = status
    if status == 500:
        frappe.response["message"] = BeautifulSoup(str(message)).get_text()
    else:
        frappe.response["message"] = message
    frappe.response["result"] = data


def method_validate(methods):
    @wrapt.decorator
    def wrapper(wrapped, instance, args, kwargs):
        if frappe.local.request.method not in methods:
            return gen_response(500, "Invalid Request Method")
        return wrapped(*args, **kwargs)

    return wrapper


@frappe.whitelist()
@method_validate(["POST"])
def income_tax_client_list(
    start=0,
    page_length=20,
):
    args = frappe.local.form_dict
    doctype = "Income Tax Client"
    itc = frappe.qb.DocType(doctype)

    # base_condition = (
    #     (itc.docstatus == 1)
    # )

    query = (
        frappe.qb.from_(itc)
        .select(
            itc.name,
            itc.itc_date,
            itc.custom_deficit_hours,
            itc.in_time,
            itc.out_time,
            itc.working_hours,
        )
        .orderby(itc.creation, order=Order.asc)
    )

    results = query.run(as_dict=True)
