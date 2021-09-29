# Sitzreservation

A simple seat reservation tool sending confirmation emails with QR-code tickets. The live version is at [tickets.tvmettmenstetten.ch](https://tickets.tvmettmenstetten.ch). A lot of this has bben hardcoded and wasn't intended to be transferred to a different site, but it shouldn't be hard to modify.

### Frontend
That's the `index.cgi`. There are options to open booking with food earlier than without and to close the option for food earlier. The form validation is done with JS (`js/validateForm.js`) and again in the python script. However, the JS-validation is not very strict (for example "0" is a valid phone number). 

Once a user booked seats they get an email with the confirmation and they can then pay the club using the information in this email.

### Backend
Calling the `optool.cgi` one gets to the admin site with options to cancel bookings, register payment, etc. Hovering over a name next to a booked seat displays the booking information. For changes in personal details it might be easier to change tehm directly in the data file.

**IMPORTANT:** Access to `optool.cgi` and the `data/` folder is done exclusively through `.htaccess` files, and might need adaptation when setting up newly.

### Code structure

`index.cgi` is the main tool, it saves the reservation-data simply in .csv files under `data/` (so no database used). `optool.cgi` is to a big extend a copy of this but with options to manage bookings. (This means most changes have to be done in both these files simultaneously.)

The file `data/numberation.txt` contains a number to numerate the bills and it can be deleted to start back at `001`.

Most configurations are in `config/config.yml`, and all displayed text should be in `config/text.yml` although this is not super consistent yet.

There are 4 log files under `log/`, two for each site (`sitzresevation` and `optool`), one with the errors only and one (`.sitzreservation_DEBUG.log`) with all the debug log from python.

## Setup

### Python
I set up a [Python venv](https://docs.python.org/3/library/venv.html) on the server. There are Bash exectution instructions on top of the files in the form of `#!../../python_tvm/bin/python` which need adaptation, in particular in `index.cgi` and `optool.cgi`. (Python files end with `.cgi` instead of `.py` because of how our hosted apache server was set up)

The current version is running on Python 3.9.4 although the version shouldn't matter. the installed modules (`pip freeze`) are
```
Pillow==8.3.1
pypng==0.0.21
PyQRCode==1.2.1
PyYAML==5.4.1
```
where I am not sure if `Pillow` is still needed or if it has been replaced by `pypng`...

### Sending emails
In the file `utils/mail.py` the email credentials to send confirmation emails are currently hardcoded. If you use GMAIL you have to "Allow less Secure Apps" in your Google account and it might be worth rewriting this bit using the [GMAIL API](https://developers.google.com/gmail/api/guides/sending).

### QR-Codes
We used an Android app ([also here on Github](https://github.com/joneugster/sitzreservation-QR)) to read the QR-codes although that one isn't very adaptable either... The QR-code just contains some booking information in plain text.

### Permissions
It might be not necessary but at some point I set writing permissions (`chmod a+w`) for certain files. 
