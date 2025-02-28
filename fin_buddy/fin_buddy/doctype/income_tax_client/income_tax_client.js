// Copyright (c) 2025, AjayRaj Mahiwal and contributors
// For license information, please see license.txt

frappe.ui.form.on("Income Tax Client", {
    client_id(frm){
        if(frm.doc.client_id){
            // fetch details
            frappe.db.get_value("Client", frm.doc.client_id, ["client_name", "username", "password", "last_income_tax_sync", "dob"]).then((r)=>{
                
                if(r.message){
                    frm.set_value("client_name", r.message.client_name);
                    frm.set_value("dob", r.message.dob);
                    frm.set_value("username", r.message.username);
                    frm.set_value("password", r.message.password);
                    frm.set_value("last_income_tax_sync", r.message.last_income_tax_sync);
                }
            })
        }
        else{
            frm.set_value("client_name", "");
            frm.set_value("username", "");
            frm.set_value("dob", "");
            frm.set_value("password", "");
            frm.set_value("last_income_tax_sync", "");
        }
    },
    refresh(frm){
        if (!frm.is_new() && !frm.doc.disabled && frm.doc.username && frm.doc.password){
            frm.add_custom_button(__("IncomeTax"), function() {
                frappe.confirm(
                    __("Are you sure you want to log ?"),  // Update the confirmation message
                    function() {
                        // Yes callback
                        frappe.call({
                            method: "fin_buddy.events.incometax_gov.login_into_portal",
                            args: {
                                client_name: frm.doc.client_id  // Pass client name to the method
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

        if (!frm.is_new() && frm.doc.client_id){
            frm.add_custom_button("Response to Outstanding Demand", function(){
                frappe.set_route("List", "Response to Outstanding Demand", { client: frm.doc.client_id });
            }, "View Notices");
            
            frm.add_custom_button("E Proceeding", function(){
                frappe.set_route("List", "E Proceeding", { client: frm.doc.client_id });
            }, "View Notices");
        }

    }
});