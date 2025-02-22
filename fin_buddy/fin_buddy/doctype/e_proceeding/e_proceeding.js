// Copyright (c) 2025, AjayRaj Mahiwal and contributors
// For license information, please see license.txt

frappe.ui.form.on("E Proceeding", {
	refresh(frm) {
        if(!frm.is_new() && !frm.doc.response_acknowledgement){
            frm.add_custom_button(__("Submit Response"), function(){
                frappe.confirm(
                    __("Are you sure you want to Submit Response ?"),
                    function(){
                        frappe.call({
                            method: "fin_buddy.events.incometax_gov.submit_response",
                            args:{
                                client_name: frm.doc.client,
                                notice_id: frm.doc.name,
                            },
                            freeze: true,
                            freeze_message: __("Queuing selected clients for processing..."),
                            callback: function(response){
                                if(response.message){
                                    frappe.msgprint(__(response.message.message));
                                }
                            }
                        })
                    }
                )
            })
        }

        if (frm.is_new()) {
            frm.set_df_property("response_message", "hidden", 1);
            frm.set_df_property("fetch_response_from_gpt", "hidden", 1);
        }
        
	},
    fetch_response_from_gpt(frm){
        if(frm.is_dirty()){
            frm.save().then(()=>{
                fetch_res_from_gpt(frm);
            });
        }
        else{
            fetch_res_from_gpt(frm);
        }
    }
});


function fetch_res_from_gpt(frm){
    frappe.call({
        method: "fin_buddy.events.incometax_gov.fetch_response_from_gpt",
        args:{
            docname: frm.doc.name
        },
        freeze: true,
        freeze_message: __("Generating Response..."),
        callback: function(response){
            if(response.message){

            }
        }
    })
}