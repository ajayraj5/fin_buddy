// // Copyright (c) 2025, AjayRaj Mahiwal and contributors
// // For license information, please see license.txt

// // frappe.ui.form.on("TDS Summary Details", {
// // 	refresh(frm) {

// // 	},
// // });

// frappe.ui.form.on("TDS Summary Details Item", {
//     show_summary: function(frm, cdt, cdn) {
//         // Get the specific child row that was clicked
//         var row = locals[cdt][cdn];
        
//         // Get the HTML content from the row
//         var html_content = row.table_html || "";
        
//         // Create and show a dialog
//         const d = new frappe.ui.Dialog({
//             title: "Summary Details",
//             fields: [{
//                 fieldtype: "HTML",
//                 fieldname: "html_content",
//                 options: html_content || "<div class='text-center'>Data not available</div>"
//             }],
//             primary_action_label: "Close",
//             primary_action: function() {
//                 d.hide();
//             }
//         });
        
//         d.show();
//     }
// });


frappe.ui.form.on("TDS Summary Details Item", {
    show_summary: function(frm, cdt, cdn) {
        // Get the specific child row that was clicked
        var row = locals[cdt][cdn];
        
        // Get the HTML content from the row
        var html_content = row.table_html || "<div class='text-center'>Data not available</div>";

        // Add custom styles for the dialog table
        let styled_html_content = `
            <style>
                table {
                    width: 100%;
                    border: 1px solid black;
                    border-collapse: collapse;
                }
                th, td {
                    border: 1px solid black;
                    padding: 8px;
                    text-align: center;
                }
                th {
                    background-color: #f2f2f2;
                }
            </style>
            ${html_content}
        `;

        // Create and show the dialog
        const d = new frappe.ui.Dialog({
            title: "Summary Details",
            fields: [{
                fieldtype: "HTML",
                fieldname: "html_content",
                options: styled_html_content
            }],
            size: 'extra-large', // small, large, extra-large 
            primary_action_label: "Close",
            primary_action: function() {
                d.hide();
            }
        });

        d.show();
    }
});
