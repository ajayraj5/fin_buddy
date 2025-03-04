import frappe
import wrapt
from bs4 import BeautifulSoup
from frappe.query_builder import Order
from frappe.query_builder.functions import Coalesce
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

    main_doc = frappe.qb.DocType(doctype)

    query = (
        frappe.qb.from_(main_doc)
        .select(
            main_doc.name.as_("id"),
            Coalesce(main_doc.client_name, "").as_("client_name"),
            Coalesce(main_doc.dob, "").as_("dob"),
            Coalesce(main_doc.username, "").as_("username"),
            Coalesce(main_doc.password, "").as_("password"),
            Coalesce(main_doc.last_income_tax_sync, "").as_(
                "last_income_tax_sync",
            ),
            Coalesce(main_doc.disabled, "").as_("disabled"),
            main_doc.creation,
            main_doc.modified,
            main_doc.owner,
            main_doc.modified_by,
        )
        .orderby(main_doc.creation, order=Order.asc)
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


@frappe.whitelist()
@method_validate(["POST"])
def income_tax_client_details():
    args = frappe.local.form_dict
    doctype = "Income Tax Client"

    record_id = args.get("id")
    if not record_id:
        return gen_response(400, "ID required to fetch det6ails!")

    if frappe.db.exists(doctype, record_id):
        record = frappe.db.get_value(
            doctype,
            record_id,
            [
                "name as id",
                "client_name",
                "dob",
                "username",
                "password",
                "disabled",
                "owner",
                "last_income_tax_sync",
                "modified_by",
                "creation",
                "modified",
            ],
            as_dict=True,
        )

        for key, value in record.items():
            if value is None:
                record[key] = ""

        return gen_response(
            200,
            "Income tax client details fetched successfully!",
            data=record,
        )
    else:
        return gen_response(
            404,
            f"Income tax client not found with id {record_id}",
        )


@frappe.whitelist()
@method_validate(["POST"])
def e_proceeding_list(
    start=0,
    page_length=20,
):
    args = frappe.local.form_dict
    search_query = args.get("search_query", "").strip().lower()
    filters = []

    doctype = "E Proceeding"

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
                doctype,
                {
                    "proceeding_name": [
                        "like",
                        f"%{search_query}%",
                    ]
                },
                "name",
            ):
                filters.append(
                    [
                        doctype,
                        "proceeding_name",
                        "like",
                        f"%{search_query}%",
                    ]
                )

            if frappe.db.get_value(
                doctype, {"client": ["like", f"%{search_query}%"]}, "name"
            ):
                filters.append(
                    [doctype, "client", "like", f"%{search_query}%"],
                )

            if frappe.db.get_value(
                doctype, {"notice_din": ["like", f"%{search_query}%"]}, "name"
            ):
                filters.append(
                    [doctype, "notice_din", "like", f"%{search_query}%"],
                )

    # doctype = "E Proceeding"
    main_doc = frappe.qb.DocType(doctype)

    query = (
        frappe.qb.from_(main_doc)
        .select(
            main_doc.name.as_("id"),
            Coalesce(main_doc.proceeding_name, "").as_("proceeding_name"),
            Coalesce(main_doc.assessment_year, "").as_("assessment_year"),
            Coalesce(main_doc.financial_year, "").as_("financial_year"),
            Coalesce(main_doc.client, "").as_("client"),
            Coalesce(main_doc.proceeding_status, "").as_("proceeding_status"),
            Coalesce(main_doc.notice_din, "").as_("notice_din"),
            Coalesce(main_doc.response_due_date, "").as_("response_due_date"),
            Coalesce(main_doc.notice_sent_date, "").as_("notice_sent_date"),
            main_doc.creation,
            main_doc.modified,
            main_doc.owner,
            main_doc.modified_by,
        )
        .orderby(main_doc.creation, order=Order.asc)
        .limit(page_length)
        .offset(start)
    )

    records = query.run(as_dict=True)

    return gen_response(
        200,
        "E Proceeding list fetched successfully",
        data=dict(
            total_records=len(records),
            records=records,
        ),
    )
