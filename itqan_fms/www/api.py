import json
import datetime
import requests
import base64
import os
from collections.abc import Iterable
from six import string_types
import frappe
from frappe.utils import flt
from frappe import _
from frappe.utils import get_files_path
from frappe.utils.file_manager import save_file
from itqan_fms.itqan_facility_management.doctype.issue.issue import get_item_details

@frappe.whitelist(allow_guest=True)
def get_user(user):
    doc = frappe.get_doc("User", user)
    if frappe.db.exists("Maintenance Worker", {"user_id": user}):
        return {"user": doc, "type": "fixer"}

    else: return {"user": doc, "type": "user"}

@frappe.whitelist()
def get_issues_list(user):

    strQuery = """
        select distinct i.name as issue, i.owner, i.tenant, t.mobile_no as tenant_number,  i.customer, i.name1 as customer_name,
        i.opening_date, i.opening_time, i.status, i.issue_type, i.priority, i.worker, i.description, i.subject,
        i.issue_image1, i.issue_image2, i.issue_image3, i.issue_image4,
        i.response_image1, i.response_image2, i.response_image3, i.response_image4,
        i.resolution_details,
        p.name as unit_number, p.building, t.deal_type
        from `tabIssue` as i
        inner join `tabTenant` as t on t.name = i.tenant
        left join `tabProperty` as p on p.name = t.property

    """
    if user!= "Administrator" and frappe.db.exists("Maintenance Worker", {"user_id": user}):
        strQuery += f""" 
        inner join `tabMaintenance Worker` as m on m.name = i.worker
        where m.user_id = '{user}'
        """

    elif user!= "Administrator" and frappe.db.exists("Tenant", {"user_id": user}):
        strQuery += f""" 
        where (t.user_id = '{user}' or i.owner = '{user}')
        """

    elif user!= "Administrator":
        strQuery += f""" 
        where i.owner = '{user}'
        """

    strQuery += " order by i.modified desc"

    res = frappe.db.sql(strQuery, as_dict = True)

    for r in res:
        issue = frappe.get_doc("Issue", r.issue)
        if issue.get("items"):
            r["items"] = []
            for item in issue.items:
                r["items"].append({
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "rate": item.rate,
                    "amount": item.amount
                })
                
    return {"docs": res}

@frappe.whitelist()
def create_issue(args):
    if isinstance(args, string_types):
        args = json.loads(args)

    if not frappe.has_permission("Issue", ptype= "write", user=args.get("owner")):
        return {"error": "Not Permitted", "status": 0}

    issue = frappe.new_doc("Issue")
    issue.update({
        "tenant": args.get("tenant"),
        "customer": args.get("customer"),
        "property": args.get("property"),
        "priority": args.get("priority"),
        "issue_type": args.get("issue_type"),
        "status": args.get("status"),
        "subject": args.get("subject"),
        "description": args.get("description"),
        "opening_date": args.get("date"),
        "opening_time": args.get("time"),
        "worker": args.get("worker")
    })

    userd = get_user(frappe.session.user)
    if userd["type"] == "fixer":
        issue.worker = frappe.db.get_value("Maintenance Worker", {"user_id": frappe.session.user}, "name")
    
    if args.get("tenant"):
        issue.name1 = frappe.db.get_value("Tenant", args.get("tenant"), "tenant_name")
    
    if args.get("items"):
        for item in args["items"]:
            item = frappe._dict(item)
            issue.append("items", frappe._dict({
                "item_code": item.item_code,
                "qty": item.qty,
                "rate": flt(item.rate),
                "amount": flt(item.rate) * flt(item.qty)
            }))

    try:
        issue.insert()

        if args.get("issue_image1"):
            res = upload_image(args.get("issue_image1"), args.get("issue_image1_name"), "Issue", issue.name, "issue_image1")
            if res.get("error"):
                return res
            issue.issue_image1 = res.get("file").file_url
            issue.save()

        if args.get("issue_image2"):
            res = upload_image(args.get("issue_image2"), args.get("issue_image2_name"), "Issue", issue.name, "issue_image2")
            if res.get("error"):
                return res
            issue.issue_image2 = res.get("file").file_url
            issue.save()

        if args.get("issue_image3"):
            res = upload_image(args.get("issue_image3"), args.get("issue_image3_name"), "Issue", issue.name, "issue_image3")
            if res.get("error"):
                return res
            issue.issue_image3 = res.get("file").file_url
            issue.save()

        if args.get("issue_image4"):
            res = upload_image(args.get("issue_image4"), args.get("issue_image4_name"), "Issue", issue.name, "issue_image4")
            if res.get("error"):
                return res
            issue.issue_image4 = res.get("file").file_url
            issue.save()

        issue.save()
        frappe.db.commit()

    except Exception as e:
        return {"error": e, "status": 0}

    return {"error": 0, "status": 1}

@frappe.whitelist()
def update_issue(args):
    if isinstance(args, string_types):
        args = json.loads(args)

    if not frappe.has_permission("Issue", ptype= "write", user=frappe.session.user):
        return {"error": "Not Permitted", "status": 0}

    if not args.get("issue"):
        return {"error": "No Issue is Specified", "status": 0}

    if not frappe.db.exists("Issue", args.get("issue")):
        return {"error": "No Issue with the Name {}".format(args.get("issue")), "status": 0}

    issue = frappe.get_doc("Issue", args.get("issue"))

    for field in args:
        print(field)
        if field == "issue": continue

        if field == "date": 
            issue.opening_date = args.get("date")

        elif field == "time":
            issue.opening_time = args.get("time")

        elif field == "issue_image1":
            issue.issue_image1 = None
            if args.get("issue_image1") != "remove":
                res = upload_image(args.get("issue_image1"), args.get("issue_image1_name"), "Issue", issue.name, "issue_image1")
                if res.get("error"):
                    return res
                issue.issue_image1 = res.get("file").file_url
            


        elif field == "issue_image2":
            issue.issue_image2 = None
            if args.get("issue_image2") != "remove":
                res = upload_image(args.get("issue_image2"), args.get("issue_image2_name"), "Issue", issue.name, "issue_image2")
                if res.get("error"):
                    return res
                issue.issue_image2 = res.get("file").file_url

        elif field == "issue_image3":
            issue.issue_image3 = None
            if args.get("issue_image3") != "remove":
                res = upload_image(args.get("issue_image3"), args.get("issue_image3_name"), "Issue", issue.name, "issue_image3")
                if res.get("error"):
                    return res
                issue.issue_image3 = res.get("file").file_url


        elif field == "issue_image4":
            issue.issue_image4 = None
            if args.get("issue_image4") != "remove":
                res = upload_image(args.get("issue_image4"), args.get("issue_image4_name"), "Issue", issue.name, "issue_image4")
                if res.get("error"):
                    return res
                issue.issue_image4 = res.get("file").file_url

        elif field == "response_image1":
            issue.response_image1 = None
            if args.get("response_image1") != "remove":
                res = upload_image(args.get("response_image1"), args.get("response_image1_name"), "Issue", issue.name, "response_image1")
                if res.get("error"):
                    return res
                issue.response_image1 = res.get("file").file_url
            


        elif field == "response_image2":
            issue.response_image2 = None
            if args.get("response_image2") != "remove":
                res = upload_image(args.get("response_image2"), args.get("response_image2_name"), "Issue", issue.name, "response_image2")
                if res.get("error"):
                    return res
                issue.response_image2 = res.get("file").file_url

        elif field == "response_image3":
            issue.response_image3 = None
            if args.get("response_image3") != "remove":
                res = upload_image(args.get("response_image3"), args.get("response_image3_name"), "Issue", issue.name, "response_image3")
                if res.get("error"):
                    return res
                issue.response_image3 = res.get("file").file_url


        elif field == "response_image4":
            print("TTTT")
            issue.response_image4 = None
            if args.get("response_image4") != "remove":
                res = upload_image(args.get("response_image4"), args.get("response_image4_name"), "Issue", issue.name, "response_image4")
                if res.get("error"):
                    return res
                issue.response_image4 = res.get("file").file_url

        elif field == "items":
            issue.update({"items": args.get("items")})

        elif hasattr(issue, field):
            print(field)
            setattr(issue, field, args.get(field))

    try:
        issue.save()
        frappe.db.commit()
    except Exception as e:
        return {"error": e, "status": 0}

    return {"error": 0, "status": 1}

@frappe.whitelist()
def get_priority_list():
    l = frappe.db.get_all("Issue Priority", fields = ["name"], as_list = 1)
    if l: l = list(flatten(l))

    return l

@frappe.whitelist()
def get_issue_type_list():
    return frappe.db.get_list("Issue Type", fields = ["name","description"])

@frappe.whitelist()
def get_project_list():
    return frappe.db.get_list("Project", fields = ["name"])

@frappe.whitelist()
def get_owners_guide_list():
    return frappe.db.get_list("Owners Guide", fields = ["subject", "text_editor_axmx"])

@frappe.whitelist()
def get_profile_info(user):
    if frappe.db.exists("Maintenance Worker", {"user_id": user}):
        user_type = "fixer"
    else: user_type = "user"

    doc = frappe.get_doc("User", user)

    if user_type == "fixer":

        return {
            "id": frappe.db.get_value("Maintenance Worker", {"user_id": user}, "name"),
            "user_name": doc.username,
            "full_name": doc.full_name,
            "phone_number": doc.mobile_no,
            "user_image": doc.user_image
        }

    else:
        contact = frappe.get_doc("Contact", {"user": user})  
        res = {
            "id": doc.name,
            "user_name": doc.username,
            "full_name": doc.full_name,
            "user_image": doc.user_image,
            "address": contact.address,
        }

        if frappe.db.exists("Tenant", {"user_id": user}):
            tenant = frappe.get_doc("Tenant", {"user_id": user})
            res["id"] = tenant.name
            res["phone_number"] = tenant.mobile_no
            res["phone_number2"] = tenant.mobile_no_2
            res["property"] = tenant.property
            res["deal_type"] = tenant.deal_type
            res["deal_date"] = tenant.deal_date
            res["deal_end_date"] = tenant.deal_end_date
            if res["property"]:
                property_doc = frappe.get_doc("Property", res["property"])
                res["building_id"] = property_doc.building
        else:
            phone_numbers = frappe.get_all("Contact Phone", {
                "parent": contact.name
            }, "phone") or ""    
            res["phone_number"] = [ph.phone for ph in phone_numbers]

        return res

@frappe.whitelist()
def update_profile_info(args):
    if isinstance(args, string_types):
        args = json.loads(args)

    if not args.get("user"):
        return {"error": "You didn't provide a user", "status": 0}

    user = frappe.get_doc("User", args.get("user"))
    if args.get("user_photo") == "remove":
        user.user_image = ""
        user.save()


    if args.get("user_photo") and args.get("photo_name"):
        res = upload_image(args.get("user_photo"), args.get("photo_name"), "User", user.name, "user_image")
        if res.get("error"):
            return res
        user.user_image = res.get("file").file_url
        user.save()

    if args.get("user_name"):
        user.username = args.get("user_name")
        user.save()

    if args.get("phone_number") or args.get("phone_number2"):
        tenant = frappe.get_doc("Tenant", {"user_id": user.name})
        tenant.mobile_no = args.get("phone_number") if args.get("phone_number") else tenant.mobile_no
        tenant.mobile_no_2
        tenant.mobile_no_2 = args.get("phone_number2") if args.get("phone_number2") else tenant.mobile_no_2
        tenant.save()

    frappe.db.commit()
    return {"error": "", "status": 1}

@frappe.whitelist()
def get_issue_items(user):
    if user == "Administrator":
        return frappe.db.sql(f"""
        select distinct i.name as row_name, i.item_code, i.rate, i.amount, i.qty, i.docstatus   
        from `tabMaintenance Order Item` as i
        inner join `tabIssue` as issue on issue.name = i.prevdoc_docname
        where i.docstatus != 2
    """, as_dict = 1)

    worker = frappe.db.get_value("Maintenance Worker", {"user_id": user})
    if not worker: 
        return


    return frappe.db.sql(f"""
        select distinct i.name as row_name, i.item_code, i.rate, i.amount, i.qty, i.docstatus   
        from `tabMaintenance Order Item` as i
        inner join `tabIssue` as issue on issue.name = i.prevdoc_docname
        where i.docstatus != 2 and issue.worker = '{worker}'
    """, as_dict = 1)

def flatten(lis):
    for item in lis:
        if isinstance(item, Iterable) and not isinstance(item, str):
            for x in flatten(item):
                yield x
        else:        
            yield item

@frappe.whitelist()
def get_items_list():
    l = frappe.db.get_all("Item", fields = ["name"], as_list = 1)
    items = []
    for item in l:
        items.append(get_item_details(item[0]))

    return items

def upload_image(base64_string, filename, dt, dn, df):
    try:
        # Decode the Base64 string
        image_data = base64.b64decode(base64_string)
        
        # Define the file path
        file_path = os.path.join(get_files_path(), filename)
        
        # Save the image to the server
        with open(file_path, 'wb') as f:
            f.write(image_data)
        
        # Save the file in Frappe's file manager
        f = save_file(filename, image_data, dt, dn, "Home", is_private = 0, decode=False, df=df)
        
        return {"status": 1, "error": "", "file": f}
    except Exception as e:
        return {"status": 0, "error": str(e), "file": None}

@frappe.whitelist()
def get_delivery_apps_list():
    return frappe.db.get_list("Application Delivery", fields = ["*"])

@frappe.whitelist()
def get_events_type_list():
    return frappe.db.get_list("Events Type", fields = ["*"])

@frappe.whitelist()
def get_permit_request(email):
    try:
        user = frappe.get_doc("User", email)

        tenants = frappe.get_all("Tenant", filters={"user_id": email}, fields=["name"])

        if not tenants:
            return []

        tenant_names = [t.name for t in tenants]

        permits = frappe.get_all(
            "Permits Request",
            filters={"custom_tenant": ["in", tenant_names]},
            fields=["name", "permit_type", "custom_tenant", "creation", "modified"]  # specify fields you want
        )

        result = []

        for permit in permits:

            permit_doc = frappe.get_doc("Permits Request", permit.name)
            permit_data = permit_doc.as_dict()


            if permit_data.get("permit_type") == "Labor":
                
                permit_data["labor_details"] = permit_data.get("table_vypp", [])
            else:
                
                permit_data.pop("table_vypp", None)

            result.append(permit_data)

        return result

    except frappe.DoesNotExistError:
        frappe.throw(f"User with email '{email}' does not exist")
    except Exception as e:
        frappe.throw(f"An error occurred: {str(e)}")


@frappe.whitelist(allow_guest=True)
def create_permit_request(data):
    try:
        
        if isinstance(data, str):
            data = json.loads(data)

        
        permit = frappe.new_doc("Permits Request")
        permit.permit_type = data.get("permit_type")
        permit.date = data.get("date")
        permit.custom_tenant = data.get("custom_tenant")
        permit.delivery_type = data.get("delivery_type")
        permit.application_delivery = data.get("application_delivery")
        permit.restaurant_name = data.get("restaurant_name")
        permit.guset_name = data.get("guset_name")
        permit.guset_relations = data.get("guset_relations")
        permit.engineer_name = data.get("engineer_name")
        permit.duration_permit = data.get("duration_permit")
        permit.id = data.get("id")
        permit.id_attach = data.get("id_attach")
        permit.start_date = data.get("start_date")
        permit.end_date = data.get("end_date")
        permit.events_type = data.get("events_type")
        permit.other_permits_type = data.get("other_permits_type")
        permit.details = data.get("details")
        permit.from_date = data.get("from_date")
        permit.to_date = data.get("to_date")

        if data.get("permit_type") == "Labor":
            labor_details = data.get("table_vypp", [])
            for labor in labor_details:
                permit.append("table_vypp", {
                    "id": labor.get("id"),
                    "work_type": labor.get("work_type"),
                    "labor_name": labor.get("labor_name"),
                })

        permit.insert()
        frappe.db.commit()

        if data.get("permit_type") == "Permit Engineer":
            id_attach_base64 = data.get("id_attach")
            if id_attach_base64:
                filename = f"{permit.name}_id_attach"
                upload_result = upload_image(id_attach_base64, filename, "Permits Request", permit.name, "id_attach")
                if upload_result["status"] == 1:
                    permit.id_attach = upload_result["file"].file_url
                    permit.insert()
                    frappe.db.commit()
                else:
                    return {"success": False, "error": f"File upload failed: {upload_result['error']}"}


        return {"success": True, "permit_name": permit.name}

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Create Permit Request Error")
        return {"success": False, "error": str(e)}



