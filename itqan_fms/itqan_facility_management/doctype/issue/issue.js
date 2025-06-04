// Copyright (c) 2024, ITQAN and contributors
// For license information, please see license.txt

frappe.ui.form.on('Issue', {
	onload_post_render: function(frm) {
		frm.get_field("items").grid.set_multiple_add("item_code", "qty");
	},
	refresh: function(frm){
		if (frm.doc.status != "Closed"){
			frm.add_custom_button(__('Maintenance Order'),
			function() {
				frm.trigger("create_maintenance_order")
			}, __('Create'));

		}
	},
	create_maintenance_order: function(frm){
		frappe.model.open_mapped_doc({
			method: "itqan_fms.itqan_facility_management.doctype.issue.issue.create_maintenance_order",
			frm: frm
		})
	}
});

frappe.ui.form.on('Issue', {
	onload_post_render: function(frm) {
		frm.get_field("items").grid.set_multiple_add("item_code", "qty");
	},
	refresh: function(frm){
			frm.add_custom_button(__('Sales Invoice'),
			function() {
				frm.trigger("create_sales_invoice")
			}, __('Create'));

		
	},
	create_sales_invoice: function(frm){
		frappe.model.open_mapped_doc({
			method: "itqan_fms.itqan_facility_management.doctype.issue.issue.create_sales_invoice",
			frm: frm
		})
	}
});

frappe.ui.form.on("Issue Item", {
	calculate: function(frm, cdt, cdn) {
		let row = frappe.get_doc(cdt, cdn);
		frappe.model.set_value(cdt, cdn, "amount", flt(row.qty) * flt(row.rate));
	},
	qty: function(frm, cdt, cdn) {
		frm.trigger("calculate", cdt, cdn);
	},
	rate: function(frm, cdt, cdn) {
		frm.trigger("calculate", cdt, cdn);
	},
	item_code: function(frm, cdt, cdn){
		let row = frappe.get_doc(cdt, cdn);
		if (row.item_code)
			get_item_details(frm, row)
		
	}
})

const get_item_details = function(frm, item){
	frappe.call({
		"method": "itqan_fms.itqan_facility_management.doctype.issue.issue.get_item_details",
		"args": {
			"item_code": item.item_code
		},
		callback: function(r){
			if (r.message){
				Object.keys(r.message).forEach(field => {
					let value = r.message[field];
					frappe.model.set_value(item.doctype, item.name, field, value);
				});

			}
		}
	})
}
