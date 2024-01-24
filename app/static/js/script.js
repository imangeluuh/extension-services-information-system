$(document).ready(function() {
    $('.filter-buttons button').click(function() {
        $('.filter-buttons button').removeClass('active'); // Remove 'active' from all buttons
        $(this).addClass('active'); // Add 'active' to the clicked button
        $('#details-container').hide();
    });

        let printBtn = document.querySelector("#print");

        printBtn.addEventListener("click", function () {
            window.print()
            // printReceipt()
        });

        // function printReceipt() {
        //     var w = window.open();

        //     w.document.write('<html><head><title></title>');
        //     w.document.write('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@tabler/core@1.0.0-beta17/dist/css/tabler.min.css">');
        //     w.document.write('<link rel="stylesheet" href="/static/css/print-report.css">');
        //     w.document.write('</head><body>');
        //     w.document.write(document.getElementById('program-report').outerHTML);
        //     const script_str = "<script type='text/javascript'>addEventListener('load', () => { print(); })<"
        //     w.document.write(script_str+"/script></body></html>");

        //     w.document.close();
        //     w.focus()

        //     // document.getElementById('program-report').focus();
        //     // document.getElementById('program-report').blur();
        //     // window.print()
        // }
    });