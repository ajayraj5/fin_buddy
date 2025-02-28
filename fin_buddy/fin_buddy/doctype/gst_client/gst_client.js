// Copyright (c) 2025, AjayRaj Mahiwal and contributors
// For license information, please see license.txt

frappe.ui.form.on("GST Client", {
    client_id(frm){
        if(frm.doc.client_id){
            // fetch details
            frappe.db.get_value("Client", frm.doc.client_id, ["client_name", "gst_username", "gst_password", "last_gst_sync"]).then((r)=>{
                
                if(r.message){
                    frm.set_value("client_name", r.message.client_name);
                    frm.set_value("gst_username", r.message.gst_username);
                    frm.set_value("gst_password", r.message.gst_password);
                    frm.set_value("last_gst_sync", r.message.last_gst_sync);
                }
            })
        }
        else{
            frm.set_value("client_name", "");
            frm.set_value("gst_username", "");
            frm.set_value("gst_password", "");
            frm.set_value("last_gst_sync", "");
        }
    },
    refresh(frm) {
        if (!frm.is_new() && !frm.doc.disabled && frm.doc.gst_username && frm.doc.gst_password){
            frm.add_custom_button(__("GST"), function() {
                frappe.confirm(
                    __("Are you sure you want to log ?"),  // Update the confirmation message
                    function() {
                        // Yes callback
                        frappe.call({
                            method: "fin_buddy.events.gst_gov.login_into_portal",
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
            frm.add_custom_button("View GST Notices", function(){
                frappe.set_route("List", "GST Notice", { client: frm.doc.client_id });
            });
        }

    },
});
