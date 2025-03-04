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


// frappe.listview_settings['GST Client'] = {
//     onload: function(listview) {
//         listview.page.add_action_item(__('Process GST Data'), function() {
//             // Get selected docs
//             const selected_docs = listview.get_checked_items();
            
//             if (selected_docs.length === 0) {
//                 frappe.msgprint(__('Please select at least one client to process.'));
//                 return;
//             }
            
//             // Get the names of selected clients
//             const client_names = selected_docs.map(doc => doc.name);
            
//             frappe.confirm(
//                 __(`Process GST data for ${selected_docs.length} selected client(s)?`),
//                 function() {
//                     // Yes callback
//                     // Process one client at a time to handle captchas
//                     process_next_client(client_names, 0, listview);
//                 },
//                 function() {
//                     // No callback
//                 }
//             );
//         });
//     }
// };

// function process_next_client(client_names, index, listview) {
//     if (index >= client_names.length) {
//         frappe.show_alert({
//             message: __("All clients processed"),
//             indicator: 'green'
//         });
//         listview.refresh();
//         return;
//     }
    
//     const client_name = client_names[index];
    
//     frappe.call({
//         method: 'fin_buddy.events.gst_gov.process_gst_client_login',
//         args: {
//             client_name: client_name
//         },
//         freeze: index === 0, // Only freeze UI for the first client
//         freeze_message: __('Initiating login for client...'),
//         callback: function(r) {
//             if (r.message && r.message.status === 'captcha_needed') {
//                 // Show captcha dialog
//                 console.log(r)
//                 show_captcha_dialog(
//                     r.message.captcha_url, 
//                     r.message.session_id,
//                     client_name,
//                     function() {
//                         // On completion (success or failure), process the next client
//                         process_next_client(client_names, index + 1, listview);
//                     }
//                 );
//             } else if (r.message && r.message.status === 'error') {
//                 frappe.show_alert({
//                     message: __(`Error processing ${client_name}: ${r.message.message}`),
//                     indicator: 'red'
//                 });
//                 // Continue with next client
//                 process_next_client(client_names, index + 1, listview);
//             } else {
//                 // If no captcha needed (unlikely in your case)
//                 frappe.show_alert({
//                     message: __(`Processed ${client_name}`),
//                     indicator: 'green'
//                 });
//                 process_next_client(client_names, index + 1, listview);
//             }
//         }
//     });
// }

// function show_captcha_dialog(captcha_url, session_id, client_name, on_complete) {
//     const d = new frappe.ui.Dialog({
//         title: __(`Enter Captcha for ${client_name}`),
//         fields: [
//             {
//                 fieldname: 'captcha_image_html',
//                 fieldtype: 'HTML',
//                 options: `<div class="text-center">
//                             <img src="${captcha_url}" alt="Captcha" style="margin-bottom: 10px; max-width: 100%;" />
//                             <p class="text-muted">${__('Please enter the text shown in the image above')}</p>
//                          </div>`
//             },
//             {
//                 label: __('Captcha Text'),
//                 fieldname: 'captcha_text',
//                 fieldtype: 'Data',
//                 reqd: 1
//             }
//         ],
//         primary_action_label: __('Submit'),
//         primary_action: function() {
//             const captcha_text = d.get_value('captcha_text');
            
//             // Show loading state
//             d.disable_primary_action();
//             d.set_message(__('Processing...'));
            
//             frappe.call({
//                 method: 'fin_buddy.events.gst_gov.submit_gst_captcha',
//                 args: {
//                     session_id: session_id,
//                     captcha_text: captcha_text
//                 },
//                 callback: function(r) {
//                     d.hide();
                    
//                     if (r.message && r.message.status === 'success') {
//                         frappe.show_alert({
//                             message: __(`Processing completed for ${client_name}`),
//                             indicator: 'green'
//                         });
//                     } else {
//                         frappe.msgprint({
//                             title: __('Error'),
//                             indicator: 'red',
//                             message: r.message ? r.message.message : __('An error occurred')
//                         });
//                     }
                    
//                     if (on_complete) on_complete();
//                 }
//             });
//         }
//     });
    
//     d.show();
// }




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
    
    // Show indicator
    frappe.show_alert({
        message: __(`Processing ${client_name}...`),
        indicator: 'blue'
    }, 5);
    
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
                show_captcha_dialog(
                    r.message.captcha_url, 
                    r.message.session_id,
                    client_name,
                    function(success) {
                        // Delay slightly before processing next client
                        setTimeout(function() {
                            process_next_client(client_names, index + 1, listview);
                        }, 1000);
                    }
                );
            } else if (r.message && r.message.status === 'error') {
                frappe.show_alert({
                    message: __(`Error processing ${client_name}: ${r.message.message}`),
                    indicator: 'red'
                });
                // Continue with next client
                setTimeout(function() {
                    process_next_client(client_names, index + 1, listview);
                }, 1000);
            } else {
                // If no captcha needed (unlikely in your case)
                frappe.show_alert({
                    message: __(`Processed ${client_name}`),
                    indicator: 'green'
                });
                setTimeout(function() {
                    process_next_client(client_names, index + 1, listview);
                }, 1000);
            }
        }
    });
}

function show_captcha_dialog(captcha_url, session_id, client_name, on_complete) {
    // Force captcha image to be loaded fresh by adding a timestamp
    const timestamped_url = `${captcha_url}?t=${new Date().getTime()}`;
    
    const d = new frappe.ui.Dialog({
        title: __(`Enter Captcha for ${client_name}`),
        fields: [
            {
                fieldname: 'captcha_image_html',
                fieldtype: 'HTML',
                options: `<div class="text-center">
                            <img src="${timestamped_url}" alt="Captcha" style="margin-bottom: 10px; max-width: 100%; border: 1px solid #ccc;" />
                            <p class="text-muted">${__('Please enter the text shown in the image above')}</p>
                            <button class="btn btn-sm btn-default refresh-captcha">
                                <i class="fa fa-refresh"></i> ${__('Refresh Captcha')}
                            </button>
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
            
            // First check if session is still valid
            frappe.call({
                method: 'fin_buddy.events.gst_gov.check_session_status',
                args: {
                    session_id: session_id
                },
                callback: function(r) {
                    if (r.message && r.message.valid) {
                        // Session is valid, proceed with submission
                        submit_captcha();
                    } else {
                        // Session is invalid, show error and get a new captcha
                        frappe.msgprint({
                            title: __('Session Error'),
                            indicator: 'red',
                            message: __('Your session has expired. Please try again.')
                        });
                        
                        d.hide();
                        
                        // Start a new session
                        frappe.call({
                            method: 'fin_buddy.events.gst_gov.process_gst_client_login',
                            args: {
                                client_name: client_name
                            },
                            callback: function(r) {
                                if (r.message && r.message.status === 'captcha_needed') {
                                    // Show a new captcha dialog
                                    show_captcha_dialog(
                                        r.message.captcha_url, 
                                        r.message.session_id,
                                        client_name,
                                        on_complete
                                    );
                                } else {
                                    frappe.msgprint({
                                        title: __('Error'),
                                        indicator: 'red',
                                        message: r.message ? r.message.message : __('An error occurred')
                                    });
                                    
                                    if (on_complete) on_complete(false);
                                }
                            }
                        });
                    }
                }
            });
            
            function submit_captcha() {
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
                            if (on_complete) on_complete(true);
                        } else {
                            frappe.msgprint({
                                title: __('Error'),
                                indicator: 'red',
                                message: r.message ? r.message.message : __('An error occurred')
                            });
                            
                            if (on_complete) on_complete(false);
                        }
                    }
                });
            }
        }
    });
    
    // Add refresh captcha functionality
    d.$wrapper.find('.refresh-captcha').on('click', function() {
        // Reload the captcha by refreshing the login process
        frappe.call({
            method: 'fin_buddy.events.gst_gov.process_gst_client_login',
            args: {
                client_name: client_name
            },
            callback: function(r) {
                if (r.message && r.message.status === 'captcha_needed') {
                    // Update session ID
                    session_id = r.message.session_id;
                    
                    // Update captcha image with timestamp to prevent caching
                    const new_captcha_url = `${r.message.captcha_url}?t=${new Date().getTime()}`;
                    d.$wrapper.find('img').attr('src', new_captcha_url);
                    
                    frappe.show_alert({
                        message: __('Captcha refreshed'),
                        indicator: 'green'
                    }, 3);
                } else {
                    frappe.msgprint({
                        title: __('Error'),
                        indicator: 'red',
                        message: r.message ? r.message.message : __('Could not refresh captcha')
                    });
                }
            }
        });
        return false;
    });
    
    d.show();
}