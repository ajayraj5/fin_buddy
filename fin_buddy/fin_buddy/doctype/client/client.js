// Copyright (c) 2025, AjayRaj Mahiwal and contributors
// For license information, please see license.txt

frappe.ui.form.on("Client", {
    refresh(frm) {
        // Show the "Login" button only if the document is not new
        if (!frm.is_new() && !frm.doc.disabled && frm.doc.username && frm.doc.password){
            frm.add_custom_button(__("IncomeTax"), function() {
                frappe.confirm(
                    __("Are you sure you want to log ?"),  // Update the confirmation message
                    function() {
                        // Yes callback
                        frappe.call({
                            method: "fin_buddy.events.incometax_gov.login_into_portal",
                            args: {
                                client_name: frm.doc.name  // Pass client name to the method
                            },
                            freeze: true,
                            freeze_message: __("Queuing selected clients for processing..."),
                            callback: function(response) {
                                // Handle the response if needed
                                if (response.message) {
                                    // frappe.msgprint(__(response.message.message));
                                    frappe.show_alert({
                                        message: __("Processing Started"),
                                        indicator: 'green'
                                    });
                                }
                            }
                        });
                    },
                    function() {
                        // No callback (Nothing to do if user clicks "No")
                    }
                );
            }, "Login");
        }

        
        if (!frm.is_new() && !frm.doc.disabled && frm.doc.gst_username && frm.doc.gst_password){
            frm.add_custom_button(__("GST"), function() {
                frappe.confirm(
                    __("Are you sure you want to log ?"),  // Update the confirmation message
                    function() {
                        // Yes callback
                        frappe.call({
                            method: "fin_buddy.events.gst_gov.login_into_portal",
                            args: {
                                client_name: frm.doc.name  // Pass client name to the method
                            },
                            freeze: true,
                            freeze_message: __("Queuing selected clients for processing..."),
                            callback: function(response) {
                                // Handle the response if needed
                                if (response.message) {
                                    // frappe.msgprint(__(response.message.message));
                                    frappe.show_alert({
                                        message: __("Processing Started"),
                                        indicator: 'green'
                                    });
                                }
                            }
                        });
                    },
                    function() {
                        // No callback (Nothing to do if user clicks "No")
                    }
                );
            }, "Login");
        }


        if (!frm.is_new() && !frm.doc.disabled && frm.doc.tds_username && frm.doc.tds_password){
            frm.add_custom_button(__("TDS"), function() {
                frappe.confirm(
                    __("Are you sure you want to log ?"),  // Update the confirmation message
                    function() {
                        // Yes callback
                        frappe.call({
                            method: "fin_buddy.events.tds_gov.login_into_portal",
                            args: {
                                client_name: frm.doc.name  // Pass client name to the method
                            },
                            freeze: true,
                            freeze_message: __("Queuing selected clients for processing..."),
                            callback: function(response) {
                                // Handle the response if needed
                                if (response.message) {
                                    // frappe.msgprint(__(response.message.message));
                                    frappe.show_alert({
                                        message: __("Processing Started"),
                                        indicator: 'green'
                                    });
                                }
                            }
                        });
                    },
                    function() {
                        // No callback (Nothing to do if user clicks "No")
                    }
                );
            }, "Login");
        }
    },
});
