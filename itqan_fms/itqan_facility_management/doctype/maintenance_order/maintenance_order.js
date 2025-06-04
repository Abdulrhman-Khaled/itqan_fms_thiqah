// Copyright (c) 2024, ITQAN and contributors
// For license information, please see license.txt

{% include 'erpnext/selling/sales_common.js' %}
frappe.provide("itqan_facility_management");

itqan_facility_management.MaintenanceOrderController = class MaintenanceOrderController extends erpnext.selling.SellingController{
	onload(doc, dt, dn) {
		super.onload(doc, dt, dn);
	}
	
}

extend_cscript(cur_frm.cscript, new itqan_facility_management.MaintenanceOrderController({frm: cur_frm}));

frappe.ui.form.on('Maintenance Order', {
	onload: function(frm) {
		if (!frm.doc.transaction_date){
			frm.set_value('transaction_date', frappe.datetime.get_today())
		}
		erpnext.queries.setup_queries(frm, "Warehouse", function() {
			return {
				filters: [
					["Warehouse", "company", "in", ["", cstr(frm.doc.company)]],
				]
			};
		});


		frm.set_query('warehouse', 'items', function(doc, cdt, cdn) {
			let row  = locals[cdt][cdn];
			let query = {
				filters: [
					["Warehouse", "company", "in", ["", cstr(frm.doc.company)]],
				]
			};
			if (row.item_code) {
				query.query = "erpnext.controllers.queries.warehouse_query";
				query.filters.push(["Bin", "item_code", "=", row.item_code]);
			}
			return query;
		});
	},
	
	delivery_date: function(frm) {
		$.each(frm.doc.items || [], function(i, d) {
			if(!d.delivery_date) d.delivery_date = frm.doc.delivery_date;
		});
		refresh_field("items");
	}
});

frappe.ui.form.on('Maintenance Order Item', {
	item_code: function(frm,cdt,cdn) {
		var row = locals[cdt][cdn];
		if (frm.doc.delivery_date) {
			row.delivery_date = frm.doc.delivery_date;
			refresh_field("delivery_date", cdn, "items");
		} else {
			frm.script_manager.copy_from_first_row("items", row, ["delivery_date"]);
		}
	},
	delivery_date: function(frm, cdt, cdn) {
		if(!frm.doc.delivery_date) {
			erpnext.utils.copy_value_in_all_rows(frm.doc, cdt, cdn, "items", "delivery_date");
		}
	}
})

