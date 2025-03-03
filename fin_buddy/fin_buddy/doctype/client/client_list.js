// frappe.listview_settings['Client'] = {
//     onload: function(listview) {
//         // Add a custom action button
//         listview.page.add_action_item(__('Process Income Tax Data'), function() {
//             // Get selected docs
//             const selected_docs = listview.get_checked_items();
            
//             if (selected_docs.length === 0) {
//                 frappe.msgprint(__('Please select at least one client to process.'));
//                 return;
//             }
            
//             // Get the names of selected clients
//             const client_names = selected_docs.map(doc => doc.name);
//             console.log(client_names);
            
//             frappe.confirm(
//                 __(`Process Income Tax data for ${selected_docs.length} selected client(s)?`),
//                 function() {
//                     // Yes callback
//                     frappe.call({
//                         method: "fin_buddy.events.incometax_gov.process_selected_clients",
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


//         listview.page.add_action_item(__('Process GST Data'), function() {
//             // Get selected docs
//             const selected_docs = listview.get_checked_items();
            
//             if (selected_docs.length === 0) {
//                 frappe.msgprint(__('Please select at least one client to process.'));
//                 return;
//             }
            
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


//         listview.page.add_action_item(__('Process TDS Data'), function() {
//             // Get selected docs
//             const selected_docs = listview.get_checked_items();
            
//             if (selected_docs.length === 0) {
//                 frappe.msgprint(__('Please select at least one client to process.'));
//                 return;
//             }
            
//             // Get the names of selected clients
//             const client_names = selected_docs.map(doc => doc.name);
//             console.log(client_names);
            
//             frappe.confirm(
//                 __(`Process TDS data for ${selected_docs.length} selected client(s)?`),
//                 function() {
//                     // Yes callback
//                     frappe.call({
//                         method: "fin_buddy.events.tds_gov.process_selected_clients",
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