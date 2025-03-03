// Copyright (c) 2025, AjayRaj Mahiwal and contributors
// For license information, please see license.txt

frappe.ui.form.on("TDS Client", {
    // client_id(frm){
    //     if(frm.doc.client_id){
    //         // fetch details
    //         frappe.db.get_value("Client", frm.doc.client_id, ["client_name", "tds_username", "tds_password", "last_tds_sync"]).then((r)=>{
                
    //             if(r.message){
    //                 frm.set_value("client_name", r.message.client_name);
    //                 frm.set_value("tds_username", r.message.tds_username);
    //                 frm.set_value("tds_password", r.message.tds_password);
    //                 frm.set_value("last_tds_sync", r.message.last_tds_sync);
    //             }
    //         })
    //     }
    //     else{
    //         frm.set_value("client_name", "");
    //         frm.set_value("tds_username", "");
    //         frm.set_value("tds_password", "");
    //         frm.set_value("last_tds_sync", "");
    //     }
    // },
    refresh(frm){
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

        if (!frm.is_new() && frm.doc.name){
            frm.add_custom_button("View TDS Notices", function(){
                frappe.set_route("List", "TDS Notice", { client: frm.doc.name });
            });
        }
    }
});
