function validateForm() {
    return false; 
    var forename = document.forms["MyForm"]["firstname"].value;
    var name = document.forms["MyForm"]["lastname"].value;
    var street = document.forms["MyForm"]["street"].value;
    var number = document.forms["MyForm"]["street_nr"].value;
    var plz = document.forms["MyForm"]["postcode"].value;
    var city = document.forms["MyForm"]["city"].value;
    var email = document.forms["MyForm"]["email"].value;
    var email2 = document.forms["MyForm"]["email_confirm"].value;
    var seat = document.forms["MyForm"]["seat"].value;
    var tel = document.forms["MyForm"]["phone"].value;
    var menus = document.forms["MyForm"]["menus"].value;
    var title = document.forms["MyForm"]["title"].value;
    var conditions = document.forms["MyForm"]["conditions"].checked;

    var tel_new = tel.replace(/[^\d+]/g, '');

    //Input validation
    if (seat===null || seat===""){
        alert("Wählen Sie mindestens einen Sitz aus!");
        return false;}
        
    if (title===null || title==='') {
        alert("Geben Sie die gewünschte Anrede an!");
        return false;}
    
    if (forename===null || forename==="" || forename.match(/^[^;]+$/)===null) {
        alert("Der Vorname ist ungültig! (Keine Semicolons ;)");
        return false;}
    
    if (name===null || name==="" || name.match(/^[^;]+$/)===null) {
        alert("Der Nachname ist ungültig! (Keine Semicolons ;)");
        return false;}
    
    if (street===null || street==="" || street.match(/^\s*[\wäöüéèàÄÖÜ\s]+\.?\s*$/)===null) {
        alert("Die Strasse ist ungültig! (nur Buchstaben inkl. ÄÖÜäöüéèà und ev. Punkt am Schluss! zB: 'Limmatstr.' oder 'im Möösli')" );
        return false;}
    
    if (number!==null && number!=="" && number.match(/^\s*[0-9]+\s*\w?\s*$/)===null) {
        alert("Die Hausnummer ist ungültig! (Bsp: 12 oder 12a oder 12A)");
        return false;}

    if (plz===null || plz==="" || plz.match(/^\s*[0-9]{4}\s*$/)===null) {
        alert("Postleitzahl ist ungültig! (4stellig)");
        return false;}

    if (city===null || city==="" || city.match(/^[^;]+$/)===null) {
        alert("Der Ort ist ungültig! (Keine Semicolons ;)");
        return false;}

    if (email===null || email==="" || email.match(/^[^;]+@[^;]+\.[^;]+$/)===null) {
        alert("Die Email-Addresse ist ungültig! (Bsp: muster@nowhere.ch, darf keine Semicolons (;) enthalten)");
        return false;}
            
    if (email != email2) {
        alert("Emailaddresse und Bestätigung stimmen nicht überein!");
        return false;}

    if (tel === null || tel === "" || tel_new.match(/^[+]?[0-9\s]{10,14}$/)===null) {
        alert("Die Telefonnummer ist ungültig! (Bsp: 0430123456 oder +41430123456)");
        return false;}
        
    //Menus
    if(document.forms["MyForm"]["menus_conf"].value == "not_used") {
        if(menus===null || menus==="") {
            alert("Geben Sie eine Anzahl Menüs an!");
            return false;}
        
        if (menus.match(/^\s*(all|[0-9]+)\s*$/)===null) {
            alert("Die Anzahl Menüs muss eine Zahl sein!");
            return false;}
    } else {
        if(document.forms["MyForm"]["Menus_Conf"].checked !== true) {
            alert("Sie müssen noch das Häckchen bei den Menüs setzen (oder warten bis die Reservation ohne Menü freigeschaltet wird).");
            return false;}
    }
    
    if (conditions !== true) {
        alert("Sie müssen noch die Bedingung akzeptieren!");
        return false;}

    return true;
}


