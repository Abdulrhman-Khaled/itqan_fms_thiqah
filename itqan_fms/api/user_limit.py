import frappe
from frappe import _

def validate_tenant_user_limit(doc, method):
    """Limit creation of Users with role Tenant to maximum 250 and block import."""

    # Is user assigned role Tenant?
    has_tenant_role = any(r.role == "Tenant" for r in doc.roles)

    if not has_tenant_role:
        return  # No tenant role → exit

    # Count existing tenant users
    tenant_count = frappe.db.count("Has Role", {"role": "Tenant"})

    # Detect if this operation is IMPORT
    is_import = bool(frappe.flags.in_import)

    # ---------- IMPORT BLOCK ----------
    if is_import:
        frappe.throw(_("Importing Tenant users is not allowed. Please create manually."))

    # ---------- NEW USER LIMIT ----------
    if doc.is_new() and tenant_count >= 250:
        frappe.throw(_("You cannot create more than 250 Tenant users Please Upgrate your Plan."))

    # ---------- EDIT EXISTING USER ----------
    if not doc.is_new() and tenant_count >= 250:
        old_roles = [
            r.role for r in frappe.get_all(
                "Has Role",
                filters={"parent": doc.name},
                fields=["role"]
            )
        ]

        # User didn’t have Tenant before, now trying to add it
        if "Tenant" not in old_roles:
            frappe.throw(_("User limit reached. Cannot assign Tenant role.You cannot create more than 250 Tenant users Please Upgrate your Plan."))
