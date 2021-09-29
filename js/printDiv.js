/*function printDiv(divName) {
    var originalContents = document.body.innerHTML;

    document.getElementById("print_button").style.display = "none";
    
    var printContents = document.getElementById(divName).innerHTML;


    //document.write('<link rel="stylesheet" type="text/css" href="css/bill.css"/>');

    document.body.innerHTML = printContents;
    window.print();
    document.body.innerHTML = originalContents;
}*/

function printDiv(elem)
{
    var mywindow = window.open('', 'PRINT', '');

    mywindow.document.write('<html><head><title>' + document.title  + '</title>');

    mywindow.document.write('<link rel="stylesheet" href="css/bill.css" type="text/css" />');
    //mywindow.document.write('<link rel="stylesheet" href="css/frontend.css" type="text/css" />');

    mywindow.document.write('</head><body><div id="bill" class="to_print">');
    mywindow.document.write('<h1>' + document.title  + '</h1>');
    mywindow.document.write(document.getElementById(elem).innerHTML);
    mywindow.document.write('</div></body></html>');

    mywindow.document.getElementById("print_button").style.display = "none";

    mywindow.document.close(); // necessary for IE >= 10
    mywindow.focus(); // necessary for IE >= 10*/

    //mywindow.print();
    //mywindow.close();

    return true;
}