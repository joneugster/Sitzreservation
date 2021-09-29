function validateOP() {
    
    var submit_opt = document.forms["MyForm"]["action"].value;
    alert(submit_opt);
    if (submit_opt==="free") {
        return confirm("Wollen Sie diese Sitze wirklich freigeben? Kann nicht rückgängig gemacht werden!");
    } else if (submit_opt==="paid") {
        
    } /*else if (submit_opt==="getinfo") {
        if (false) {//das stimmt noch nicht!!!
            alert("Wählen Sie nur einen Sitz aus!");
            return false; }*/
    } else if (submit_opt==="reserve") {
        var forename = document.forms["MyForm"]["Forename"].value;
        var name = document.forms["MyForm"]["Name"].value;
        var street = document.forms["MyForm"]["Street"].value;
        var number = document.forms["MyForm"]["Number"].value;
        var plz = document.forms["MyForm"]["Plz"].value;
        var city = document.forms["MyForm"]["City"].value;
        var email = document.forms["MyForm"]["Email"].value;
        var email2 = document.forms["MyForm"]["Email_confirm"].value;
        var front1 = document.forms["MyForm"]["front1"].value;
        var front2 = document.forms["MyForm"]["front2"].value;
        var back1 = document.forms["MyForm"]["back1"].value;
        var back2 = document.forms["MyForm"]["back2"].value;
        //Test, dass alle Pflichtfelder ausgefuellt sind.
        if ((front1===null || front1==="") && (front2===null || front2==="") && (back1===null || back1==="") && (back2===null || back2==="")) {
            alert("Wählen Sie mindestens einen Sitz aus!");
            return false;
        }
        if (forename===null || name===null || street===null || plz===null || city===null || email===null || email2===null || forename==="" || name==="" || street==="" || plz==="" || city==="" || email==="" || email2==="") {
            alert("Bitte füllen Sie alle Pflichtfelder (*) aus!");
            return false;
        }
    
        // Input validation
        if (forename.match(/[^,]+/)===null) {
            alert("Der Vorname ist ungültig!");
            return false;
        }
        if (name.match(/[^,]+/)===null) {
            alert("Der Nachname ist ungültig!");
            return false;
        }
        if (street.match(/^\s*[\wäöüéèàÄÖÜ]+\.?\s*$/)===null) {
            alert("Die Strasse ist ungültig!");
            return false;
        }
        if (!(number===null || number==="")) {
            if (number.match(/^\s*[0-9]+\s*\w?\s*$/)===null) {
                alert("Die Hausnummer ist ungültig!");
                return false;
            }
        }
        if (plz.match(/^\s*[0-9]{4,10}\s*$/)===null) {
            alert("Postleitzahl ist ungültig!");
            return false;
        }
        if (city.match(/^[^,]+$/)===null) {
            alert("Der Ort ist ungültig!");
            return false;
        }
        //E-Mail
        if (email != email2) {
            alert("Emailaddresse und Bestätigung stimmen nicht überein!");
            return false;
        }
        if (email.match(/^[^,]+@[^,]+\.[^,]+$/)===null) {
            alert("Die Email-Addresse ist ungültig!");
            return false;
        }
    } 
    return false;
}

