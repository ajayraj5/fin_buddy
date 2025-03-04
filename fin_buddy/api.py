import frappe
import wrapt
from bs4 import BeautifulSoup
from frappe.query_builder import Order
from frappe.query_builder.functions import Coalesce
from frappe.utils import getdate, cstr
from frappe.utils.file_manager import save_file


def gen_response(
    status,
    message,
    data=[],
    **kwargs,
):
    frappe.response["http_status_code"] = status
    if status == 500:
        frappe.response["message"] = BeautifulSoup(str(message)).get_text()
    else:
        frappe.response["message"] = message

    if kwargs:
        frappe.response.update(kwargs)

    if data:
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
                "last_income_tax_sync",
                "owner",
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
    client = args.get("client", None)
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

    if client:
        query = query.where(main_doc.client == client)

    records = query.run(as_dict=True)

    return gen_response(
        200,
        "E Proceeding list fetched successfully",
        data=dict(
            total_records=len(records),
            records=records,
        ),
    )


def get_file_full_url(file_url):
    file_full_url = frappe.utils.get_url(file_url)
    return file_full_url
    # return f"{base_url}{file_url}"


@frappe.whitelist()
@method_validate(["POST"])
def e_proceeding_details():
    args = frappe.local.form_dict
    doctype = "E Proceeding"

    record_id = args.get("id")
    if not record_id:
        return gen_response(400, "ID required to fetch det6ails!")

    if frappe.db.exists(doctype, record_id):
        record = frappe.db.get_value(
            doctype,
            record_id,
            [
                "name as id",
                "client",
                "proceeding_name",
                "assessment_year",
                "financial_year",
                "proceeding_status",
                "notice_din",
                "response_due_date",
                "notice_sent_date",
                "notice_section",
                "notice_communication_reference_id as document_reference_id",
                "response_acknowledgement",
                "notice_letter",
                "user_input",
                "mask_this_data",
                "response_message",
                "is_terms_and_conditions_checked",
                "owner",
                "modified_by",
                "creation",
                "modified",
            ],
            as_dict=True,
        )

        reply_records = frappe.db.get_values(
            "E Proceeding Reply",
            {
                "parent": record_id,
                "parenttype": "E Proceeding",
            },
            [
                "name as id",
                "file",
                "file_name",
            ],
            as_dict=True,
        )

        other_document_records = frappe.db.get_values(
            "Attachment Item",
            {
                "parent": record_id,
                "parenttype": "E Proceeding",
            },
            [
                "name as id",
                "file",
            ],
            as_dict=True,
        )

        record["replies"] = []
        record["other_documents"] = []

        if reply_records:
            for temp in reply_records:
                for key, value in temp.items():
                    if value is None:
                        temp[key] = ""

                    if key == "file" and value and "http" not in value:
                        temp[key] = get_file_full_url(value)

            record["replies"] = reply_records

        if other_document_records:
            for temp in other_document_records:
                for key, value in temp.items():
                    if value is None:
                        temp[key] = ""

                    if key == "file" and value and "http" not in value:
                        temp[key] = get_file_full_url(value)

            record["other_documents"] = other_document_records

        for key, value in record.items():
            if value is None:
                record[key] = ""

            if key == "notice_letter" and value and "http" not in value:
                record[key] = get_file_full_url(value)

        return gen_response(
            200,
            "E proceeding details fetched successfully!",
            data=record,
        )
    else:
        return gen_response(
            404,
            f"E proceeding not found with id {record_id}",
        )


@frappe.whitelist()
@method_validate(["POST"])
def upload_file():
    try:
        if "file" not in frappe.request.files:
            frappe.throw("No file uploaded")

        args = frappe.local.form_dict

        is_private = args.get("is_private", 0)

        if is_private:
            is_private = 1
        else:
            is_private = 0

        uploaded_file = frappe.request.files["file"]
        file_doc = save_file(
            uploaded_file.filename,
            uploaded_file.stream.read(),
            None,
            None,
            is_private=is_private,
        )

        file_url = get_file_full_url(file_doc.file_url)

        return gen_response(
            200,
            "File uploaded successfully",
            file_url=file_url,
        )
    except Exception as ex:
        return gen_response(
            500,
            cstr(ex),
        )


@frappe.whitelist()
@method_validate(["POST"])
def response_to_outstanding_demand_list(
    start=0,
    page_length=20,
):
    args = frappe.local.form_dict
    search_query = args.get("search_query", "").strip().lower()
    client = args.get("client", None)
    filters = []

    doctype = "Response to Outstanding Demand"

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
                    "demand_reference_no": [
                        "like",
                        f"%{search_query}%",
                    ]
                },
                "name",
            ):
                filters.append(
                    [
                        doctype,
                        "demand_reference_no",
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
                doctype,
                {
                    "section_code": [
                        "like",
                        f"%{search_query}%",
                    ]
                },
                "name",
            ):
                filters.append(
                    [doctype, "section_code", "like", f"%{search_query}%"],
                )

            if frappe.db.get_value(
                doctype,
                {
                    "response_type": [
                        "like",
                        f"%{search_query}%",
                    ]
                },
                "name",
            ):
                filters.append(
                    [doctype, "response_type", "like", f"%{search_query}%"],
                )

            if frappe.db.get_value(
                doctype,
                {
                    "rectification_rights": [
                        "like",
                        f"%{search_query}%",
                    ]
                },
                "name",
            ):
                filters.append(
                    [
                        doctype,
                        "rectification_rights",
                        "like",
                        f"%{search_query}%",
                    ],
                )

    # doctype = "E Proceeding"
    main_doc = frappe.qb.DocType(doctype)

    query = (
        frappe.qb.from_(main_doc)
        .select(
            main_doc.name.as_("id"),
            Coalesce(main_doc.demand_reference_no, "").as_(
                "demand_reference_no",
            ),
            Coalesce(main_doc.assessment_year, "").as_("assessment_year"),
            Coalesce(main_doc.outstanding_demand_amount, "").as_(
                "outstanding_demand_amount",
            ),
            Coalesce(main_doc.client, "").as_("client"),
            Coalesce(main_doc.section_code, "").as_("section_code"),
            Coalesce(main_doc.mode_of_service, "").as_("mode_of_service"),
            Coalesce(main_doc.rectification_rights, "").as_(
                "rectification_rights",
            ),
            Coalesce(main_doc.response_type, "").as_("response_type"),
            main_doc.creation,
            main_doc.modified,
            main_doc.owner,
            main_doc.modified_by,
        )
        .orderby(main_doc.creation, order=Order.asc)
        .limit(page_length)
        .offset(start)
    )

    if client:
        query = query.where(main_doc.client == client)

    records = query.run(as_dict=True)

    return gen_response(
        200,
        f"{doctype} list fetched successfully",
        data=dict(
            total_records=len(records),
            records=records,
        ),
    )
