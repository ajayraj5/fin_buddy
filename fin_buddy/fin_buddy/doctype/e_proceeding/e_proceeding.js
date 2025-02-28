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
            frm.set_df_property("view_data_before_response_generation", "hidden", 1);
            frm.set_df_property("user_input", "hidden", 1);
            frm.set_df_property("other_documents", "hidden", 1);
            frm.set_df_property("mask_this_data", "hidden", 1);
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
    },
    view_data_before_response_generation(frm){
        if(frm.is_dirty()){
            frm.save().then(()=>{
                fetch_res_before_gpt(frm);
            });
        }
        else{
            fetch_res_before_gpt(frm);
        }
    }
});


function fetch_res_from_gpt(frm){
    frappe.call({
        method: "fin_buddy.events.incometax_gov.fetch_response_from_gpt",
        args:{
            doctype: "E Proceeding",
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

function fetch_res_before_gpt(frm){
    frappe.call({
        method: "fin_buddy.events.incometax_gov.fetch_response_from_gpt",
        args:{
            doctype: "E Proceeding",
            docname: frm.doc.name,
            is_view_data_before_response_generation: true
        },
        freeze: true,
        freeze_message: __("View Data Before Response. Generation..."),
        callback: function(response){
            if(response.message){
                console.log(response)
                let d = new frappe.ui.Dialog({
                    title: "Data",
                    fields:[
                        {
                            label: "",
                            fieldname: "data_before_generation",
                            fieldtype: "Code",
                            options: "Text", // Specify the language for the code editor
                            read_only: 1,
                        }
                    ],
                    size: "large",
                    primary_action_label: "Close",
                    primary_action: function(values){
                        // do nothing and hide
                        d.hide()
                    }
                });

                d.set_value('data_before_generation', response.message.data);
                d.show();
            }
        }
    })
}