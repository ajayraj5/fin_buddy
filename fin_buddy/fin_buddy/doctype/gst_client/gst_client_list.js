// frappe.listview_settings['GST Client'] = {
//     onload: function(listview) {

//         listview.page.add_action_item(__('Process GST Data'), function() {
//             // Get selected docs
//             const selected_docs = listview.get_checked_items();
            
//             if (selected_docs.length === 0) {
//                 frappe.msgprint(__('Please select at least one client to process.'));
//                 return;
//             }
//             console.log(selected_docs)
//             // Get the names of selected clients
//             const client_names = selected_docs.map(doc => doc.name);
//             console.log(client_names);
            
//             frappe.confirm(
//                 __(`Process GST data for ${selected_docs.length} selected client(s)?`),
//                 function() {
//                     // Yes callback
//                     frappe.call({
//                         method: "fin_buddy.events.gst_gov.process_selected_clients",
//                         args: {
//                             client_names: client_names
//                         },
//                         freeze: true,
//                         freeze_message: __('Queuing selected clients for processing...'),
//                         callback: function(response) {
                           
//                             frappe.show_alert({
//                                 message: __("Processing Started"),
//                                 indicator: 'green'
//                             });
                            
//                             // Refresh the list to show updated status
//                             listview.refresh();
//                         }
//                     });
//                 },
//                 function() {
//                     // No callback
//                 }
//             );
//         });
//     }
// };


frappe.listview_settings['GST Client'] = {
    onload: function(listview) {
        listview.page.add_action_item(__('Process GST Data'), function() {
            // Get selected docs
            const selected_docs = listview.get_checked_items();
            
            if (selected_docs.length === 0) {
                frappe.msgprint(__('Please select at least one client to process.'));
                return;
            }
            
            // Get the names of selected clients
            const client_names = selected_docs.map(doc => doc.name);
            
            frappe.confirm(
                __(`Process GST data for ${selected_docs.length} selected client(s)?`),
                function() {
                    // Yes callback
                    // Process one client at a time to handle captchas
                    process_next_client(client_names, 0, listview);
                },
                function() {
                    // No callback
                }
            );
        });
    }
};

function process_next_client(client_names, index, listview) {
    if (index >= client_names.length) {
        frappe.show_alert({
            message: __("All clients processed"),
            indicator: 'green'
        });
        listview.refresh();
        return;
    }
    
    const client_name = client_names[index];
    
    frappe.call({
        method: 'fin_buddy.events.gst_gov.process_gst_client_login',
        args: {
            client_name: client_name
        },
        freeze: index === 0, // Only freeze UI for the first client
        freeze_message: __('Initiating login for client...'),
        callback: function(r) {
            if (r.message && r.message.status === 'captcha_needed') {
                // Show captcha dialog
                console.log(r)
                show_captcha_dialog(
                    r.message.captcha_url, 
                    r.message.session_id,
                    client_name,
                    function() {
                        // On completion (success or failure), process the next client
                        process_next_client(client_names, index + 1, listview);
                    }
                );
            } else if (r.message && r.message.status === 'error') {
                frappe.show_alert({
                    message: __(`Error processing ${client_name}: ${r.message.message}`),
                    indicator: 'red'
                });
                // Continue with next client
                process_next_client(client_names, index + 1, listview);
            } else {
                // If no captcha needed (unlikely in your case)
                frappe.show_alert({
                    message: __(`Processed ${client_name}`),
                    indicator: 'green'
                });
                process_next_client(client_names, index + 1, listview);
            }
        }
    });
}

function show_captcha_dialog(captcha_url, session_id, client_name, on_complete) {
    const d = new frappe.ui.Dialog({
        title: __(`Enter Captcha for ${client_name}`),
        fields: [
            {
                fieldname: 'captcha_image_html',
                fieldtype: 'HTML',
                options: `<div class="text-center">
                            <img src="${captcha_url}" alt="Captcha" style="margin-bottom: 10px; max-width: 100%;" />
                            <p class="text-muted">${__('Please enter the text shown in the image above')}</p>
                         </div>`
            },
            {
                label: __('Captcha Text'),
                fieldname: 'captcha_text',
                fieldtype: 'Data',
                reqd: 1
            }
        ],
        primary_action_label: __('Submit'),
        primary_action: function() {
            const captcha_text = d.get_value('captcha_text');
            
            // Show loading state
            d.disable_primary_action();
            d.set_message(__('Processing...'));
            
            frappe.call({
                method: 'fin_buddy.events.gst_gov.submit_gst_captcha',
                args: {
                    session_id: session_id,
                    captcha_text: captcha_text
                },
                callback: function(r) {
                    d.hide();
                    
                    if (r.message && r.message.status === 'success') {
                        frappe.show_alert({
                            message: __(`Processing completed for ${client_name}`),
                            indicator: 'green'
                        });
                    } else {
                        frappe.msgprint({
                            title: __('Error'),
                            indicator: 'red',
                            message: r.message ? r.message.message : __('An error occurred')
                        });
                    }
                    
                    if (on_complete) on_complete();
                }
            });
        }
    });
    
    d.show();
}