import frappe
import wrapt
from bs4 import BeautifulSoup
from frappe.query_builder import Order
from frappe.utils import getdate, cstr


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
    search_query = args.get("search_query", "").strip().lower()
    filters = []

    doctype = "Income Tax Client"

    if search_query:
        date_parts = search_query.split(" to ")

        if len(date_parts) == 2:
            try:
                from_date = getdate(date_parts[0].strip())
                to_date = getdate(date_parts[1].strip())
                filters.append(
                    [
                        doctype,
                        "creation",
                        "Between",
                        [from_date, to_date],
                    ]
                )
            except ValueError:
                return gen_response(
                    400,
                    "Invalid date range format. \
Please use 'YYYY-MM-DD to YYYY-MM-DD'.",
                )
        else:
            if frappe.db.get_value(
                doctype, {"name": ["like", f"%{search_query}%"]}, "name"
            ):
                filters.append([doctype, "name", "like", f"%{search_query}%"])

            if frappe.db.get_value(
                doctype, {"username": ["like", f"%{search_query}%"]}, "name"
            ):
                filters.append(
                    [
                        doctype,
                        "username",
                        "like",
                        f"%{search_query}%",
                    ]
                )

            if frappe.db.get_value(
                doctype, {"client_name": ["like", f"%{search_query}%"]}, "name"
            ):
                filters.append(
                    [doctype, "client_name", "like", f"%{search_query}%"],
                )

    itc = frappe.qb.DocType(doctype)

    query = (
        frappe.qb.from_(itc)
        .select(
            itc.name.as_("id"),
            itc.client_name,
            itc.dob,
            itc.username,
            itc.password,
            itc.last_income_tax_sync,
            itc.disabled,
            itc.creation,
            itc.modified,
            itc.owner,
            itc.modified_by,
        )
        .orderby(itc.creation, order=Order.asc)
        .limit(page_length)
        .offset(start)
    )

    records = query.run(as_dict=True)

    return gen_response(
        200,
        "Income tax client list fetched successfully",
        data=dict(
            total_records=len(records),
            records=records,
        ),
    )


@frappe.whitelist()
@method_validate(["POST"])
def create_income_tax_client():
    args = frappe.local.form_dict
    doctype = "Income Tax Client"

    client_name = args.get("client_name")
    dob = args.get("dob")
    username = args.get("username")
    password = args.get("password")

    if not all([client_name, username, password]):
        return gen_response(
            400,
            "Client Name, Username & Password is required!",
        )

    try:
        record = frappe.get_doc(
            {
                "doctype": doctype,
                "client_name": client_name,
                "username": username,
                "password": password,
                "dob": dob,
            }
        )

        record.insert()
        frappe.db.commit()
        return gen_response(
            200,
            "Income tax client created successfully",
            data=record.as_dict(),
        )
    except Exception as ex:
        return gen_response(
            500,
            cstr(ex),
        )
