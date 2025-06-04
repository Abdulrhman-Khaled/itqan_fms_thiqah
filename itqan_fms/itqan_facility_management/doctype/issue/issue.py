# Copyright (c) 2024, ITQAN and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.desk.form.assign_to import add as add_assignment, remove
from frappe.model.mapper import get_mapped_doc
from frappe.utils import today
from erpnext.stock.get_item_details import get_price_list_rate_for

class Issue(Document):
	def validate(self):
		if self.is_new(): return

		if self.has_value_changed("worker"):
			if self.worker:
				user_id = frappe.db.get_value("Maintenance Worker", self.worker, "user_id")
				add_assignment({"doctype": self.doctype, "name": self.name, "assign_to": [user_id]})

			if self.get_doc_before_save():
				previous_user = frappe.db.get_value("Maintenance Worker", self.get_doc_before_save().worker, "user_id")
				remove(self.doctype, self.name, previous_user)

		for item in self.items:
			if not item.qty: item.qty = 1

			item.amount = item.qty * item.rate

	def after_insert(self):
		if self.worker:
			user_id = frappe.db.get_value("Maintenance Worker", self.worker, "user_id")
			add_assignment({"doctype": self.doctype, "name": self.name, "assign_to": [user_id]})


@frappe.whitelist()
def create_maintenance_order(source_name, target_doc=None):
	def set_missing_values(source, target):
		from erpnext.controllers.accounts_controller import get_default_taxes_and_charges

		maintenance_order = frappe.get_doc(target)

		company_currency = frappe.get_cached_value("Company", maintenance_order.company, "default_currency")

		if company_currency == maintenance_order.currency:
			exchange_rate = 1
		else:
			exchange_rate = get_exchange_rate(
				maintenance_order.currency, company_currency, maintenance_order.transaction_date, args="for_selling"
			)

		maintenance_order.conversion_rate = exchange_rate

		# get default taxes
		taxes = get_default_taxes_and_charges(
			"Sales Taxes and Charges Template", company=maintenance_order.company
		)
		if taxes.get("taxes"):
			maintenance_order.update(taxes)


	doclist = get_mapped_doc(
		"Issue",
		source_name,
		{
			"Issue": {"doctype": "Maintenance Order"},
			"Issue Item": {"doctype": "Maintenance Order Item", "field_map": {"parent": "prevdoc_docname", "uom": "stock_uom"}},
		},
		target_doc,
		set_missing_values,
	)

	return doclist

@frappe.whitelist()
def create_sales_invoice(source_name, target_doc=None):
	def set_missing_values(source, target):
		from erpnext.controllers.accounts_controller import get_default_taxes_and_charges

		sales_invoice = frappe.get_doc(target)

		# Assuming you want to set default values related to the company
		company_currency = frappe.get_cached_value("Company", sales_invoice.company, "default_currency")
		if company_currency == sales_invoice.currency:
			exchange_rate = 1
		else:
			exchange_rate = get_exchange_rate(
				sales_invoice.currency, company_currency, sales_invoice.transaction_date, args="for_selling"
			)

		sales_invoice.conversion_rate = exchange_rate

		# Get default taxes
		taxes = get_default_taxes_and_charges(
			"Sales Taxes and Charges Template", company=sales_invoice.company
		)
		if taxes.get("taxes"):
			sales_invoice.update(taxes)

	doclist = get_mapped_doc(
		"Issue",
		source_name,
		{
			"Issue": {"doctype": "Sales Invoice"},
			"Issue Item": {"doctype": "Sales Invoice Item", "field_map": {"parent": "prevdoc_docname", "uom": "stock_uom"}},
		},
		target_doc,
		set_missing_values,
	)

	return doclist


@frappe.whitelist()
def get_item_details(item_code):
	res = frappe.db.get_value('Item', {'item_code': item_code}, ['stock_uom', "item_name", "description", "image"], as_dict = 1)
	res["uom"] = res["stock_uom"]

	price_list = frappe.db.get_single_value("Selling Settings", "selling_price_list")
	res.rate = get_price_list_rate_for({
		"price_list": price_list,
		"uom": res["uom"],
		"transaction_date": today(),
		"ignore_party": True,
		"qty": 1
	}, item_code) or 0

	return res