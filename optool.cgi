#!../../python_tvm/bin/python
# -*- coding: utf-8 -*-
"""
Seat reservation tool for TV Mettmenstetten.

This is thought as CGI-script that produces HTML5 code.

Important:
    Make sure the files `sitzreservation.log`, `.sitzreservation_DEBUG.log`
    and all files under `data/` have permissions 'a+w',
    i.e. 'rw-rw-rw', otherwise the CGI runner will not have permissions
    to write.
"""
##### pylint: disable=invalid-name

import cgi
import logging
import os
import re
import time
import traceback
from string import Template

import yaml

from utils import seat, log_setup
# from utils.mail import send_email
from utils.html import str2html, html2utf8, error_to_html, str2htmlascii
import dynamic_parts_op as dyn

print('Content-Type: text/html; charset=utf-8')    # HTML is following
print('')                                        # blank line, end of headers

try:
    log_setup.setup(logfile='log/optool.log', color=True,
                debug_file=True, lvl_bash=logging.DEBUG, lvl_file=logging.DEBUG,
                symlink=None)
except Exception:
    logging.error('Could not open log-file.')
    logging.error(traceback.format_exc())


try:
    # Get config and text
    try:
        with open('config/text.yml', 'r',encoding='utf8') as f:
            text = yaml.load(f)
            for key, val in text.items():
                if key in ['mail_msg_bill', 'mail_msg_bill_reminder',
                           'mail_ticket_template', 'mail_wrapper']:
                    continue
            
                if isinstance(val, str):
                    val = str2html(val)
                    val = re.sub(r'\[b\](.*?)\[/b\]', r'<strong>\1</strong>', val)
                    val = re.sub(r'\[i\](.*?)\[/i\]', r'<i>\1</i>', val)
                    val = val.replace(r'\t', '&nbsp;'*4)
                    text[key] = val
    except FileNotFoundError:
        logging.error('Text file not found!')
    try:
        with open('config/config.yml', 'r', encoding='utf8') as f:
            config = yaml.load(f)
    except FileNotFoundError:
        logging.error('Config file not found!')

    # Get submitted form data
    form = cgi.FieldStorage()
    day = form.getvalue('day', None)
    submitted = (str(form.getvalue('submit', None)).lower() == 'submit')
    submit_action = form.getvalue('action', None)
    submitted_billnr = form.getvalue('bill_nr', '')
    
    if submitted and day is None:
        day = form.getvalue('day_memory', None)
    submitted_data = {key: html2utf8(form.getvalue(key, '')).strip().replace(',','') for key in
                      ['title', 'firstname', 'lastname', 'street', 'street_nr',
                       'postcode', 'city', 'address_supplement_1',
                       'address_supplement_2', 'email', 'email_confirm',
                       'comment', 'send_email']}
    submitted_data['phone'] = html2utf8(re.sub(r'\s+', '',
                                               form.getvalue('phone', ''))).strip().replace(',','')
    submitted_data['seats'] = form.getvalue('seat', list())
    if isinstance(submitted_data['seats'], str):
        submitted_data['seats'] = [submitted_data['seats']]

    # Generate dynamic parts of the site
    dynamic = {'_bill': '',
               '_room':'',
               '_general_info': '',
               '_form':'',
               '_day_selection': '',
               '_status': '',
               '_menulist': '',
               '_pricelist': '',
               '_legend': '',
               '_download': '',
               '_statistics': '',
               '_mainbody': ''
               }

    # Top navigation & day selection
    if day is not None:
        dynamic['_topnav_current_day'] = ('<li id="topnav_choice"><a>{}: '
                                          '{}</a></li>'.format(
                                              text['title_chosen_day'],
                                              text['days'][day]))
    else:
        dynamic['_topnav_current_day'] = ''
    dynamic['_day_selection'] = dyn.create_day_selection(day, text,
                                                         submitted)

    if day is not None:
        _t = time.localtime()
        is_open = (_t >= time.strptime(config['time_open'][day],
                                       '%d.%m.%Y, %H:%M'))
        is_closed = (_t > time.strptime(config['time_close'][day],
                                        '%d.%m.%Y, %H:%M'))
        force_menu = (_t < time.strptime(config['time_force_menu'][day],
                                         '%d.%m.%Y, %H:%M'))
        is_menu_closed = (_t > time.strptime(config['time_menu_close'][day],
                                             '%d.%m.%Y, %H:%M'))

        # Read in reservation data
        file = config['files'][day]
        if not os.path.exists(file):
            logging.warning('Creating new data file %s.', file)
            seat.create_file(file, columns=config['csv_columns'])
        data = seat.get_seat_info(file)

        # Create element above the seat selection
        # here we display informations about whether the reservation
        # has been successful
        _s = ''
        if is_closed:
            _s += '<p class="warn_date">${warning_reservation_closed}</p>'
#             _s += ('<button type="button" onclick="showhide('
#                    '\'wrapper_reservation\')">${button_show_seats}</button>')
        elif not is_open:
            _s += '<p class="warn_date">${warning_reservation_not_open}</p>'
        dynamic['_status'] = _s

        # Action
        if submitted:
            if submit_action == 'reserve':
                dynamic['_bill'] += dyn.do_reservation(submitted_data, text,
                                                      force_menu,
                                                      is_menu_closed, data,
                                                      form, day, config, file)
            
            else:
                submitted_billnr = [x.strip() for x in submitted_billnr.split(',')]
                submitted_billnr = [x for x in submitted_billnr if x]

                _count = len(submitted_data['seats'])
                submitted_data['seats'] = set(submitted_data['seats'])
                for n, s in data.items():
                    if s.bill_nr in submitted_billnr:
                        submitted_data['seats'].add(n) 
                        _count += 1               
                if not(submitted_data['seats']):
                    dynamic['_bill'] += '<p class="warning">${validation_no_seats_or_bill}</p>'
                else:
                    dynamic['_bill'] += Template('<p class="warning">${op_found_number_seats}: ${nr}</p>').safe_substitute(nr=_count)
                
                    if submit_action == 'free':
                        changes, _s = dyn.free_seat(submitted_data['seats'], data)
                    elif submit_action == 'paid':
                        changes, _s = dyn.seat_paid(submitted_data['seats'], data)
                    elif submit_action == 'delete_payment':
                        changes, _s = dyn.delete_payment(submitted_data['seats'], data)
                    elif submit_action == 'resend_bill':
                        changes, _s = dyn.resend_bill(submitted_data['seats'], data , day, text)
                    else:
                        changes = None
                        _s = ''
                    dynamic['_bill'] += _s
                    if changes is not None:
                        failed = dyn.apply_changes(changes, config['files'][day], 'OP')
                submitted_data['seats'] = list(submitted_data['seats'])
            data = seat.get_seat_info(file)

        # create other dynamic parts

        dynamic['_pricelist'] = dyn.create_price_list(text)
        dynamic['_menulist'] = dyn.create_menu_list(text, day)
        dynamic['_legend'] = dyn.create_legend(is_closed)
        dynamic['_room'] = dyn.create_room(submitted_data['seats'], data, config)


        dynamic['_form'] = dyn.create_address_form(form, force_menu,
                                                       is_menu_closed)

        dynamic['_download'] = Template(
            '<p class="instruction">${op_download_data}:</p>'
            '<a href="${file}" target="_blank" class="button" '
            'download>${name} herunterladen'
            '</a>').safe_substitute(file=file, name=os.path.basename(file))
            
        dynamic['_statistics'] = dyn.create_stats(data, config)
                
        dynamic['_mainbody'] = """
        <p class="instruction">${op_title_seats}:</p>            
        <button onclick="showhide('wrapper_reservation')" type="button">${op_show_reservation}</button>
        <div id="wrapper_reservation" style="display:block;">
          <aside id="pricelist">${_pricelist}</aside>
          <aside id="menulist">${_menulist}</aside>
          <aside id="legend">${_legend}</aside>
          ${_room}
          
          ${_form}
        </div>
        
        
        <fieldset id="fieldset_action">
            <legend>${op_action}</legend>
            <p>
                <input type="radio" id="reserve" name="action" value="reserve">
                <label for="reserve">${op_action_claim}</label>
            </p>
            <p><hr></p>
            <p>
                <input type="radio" id="paid" name="action" value="paid" checked>
                <label for="paid">${op_action_paid}</label>
            </p>
            <p>
                <input type="radio" id="free" name="action" value="free">
                <label for="free">${op_action_free}</label>
            </p>
            <p>
                <input type="radio" id="delete_payment" name="action" value="delete_payment">
                <label for="delete_payment">${op_action_cancel_payment}</label>
            </p>
            <p>
                <input type="radio" id="resend_bill" name="action" value="resend_bill">
                <label for="resend_bill">${op_action_bill_date}</label>
            </p>
            <p>
                <textarea  id="textarea_billnr" type="text" name="bill_nr" value="" class="address" placeholder="SA1-EUG-001, SA1-KEL-002"></textarea>
                <label for="bill_nr" class="address">${op_form_bill_nr}</label>
            </p>

        </fieldset>
        <noscript><p class="warning">${might_take_a_while}</p></noscript>
        <button id="submit_button" name="submit" value="Submit" type="submit" onclick="showhide('info_may_take_a_while')">${op_action_button}</button>
        <p id="info_may_take_a_while" style="display:none;">${might_take_a_while}</p>
"""

    # Finally we put everything together and create the html
    # ------------------------------------------------------
    with open('config/template_op.html', 'r') as f:
        content = Template(f.read())
    # First substitute the dynamic parts
    content = Template(content.safe_substitute(_mainbody=dynamic['_mainbody']))
    content = Template(content.safe_substitute(**dynamic))
    # Then plug in all the text
    content = Template(content.safe_substitute(**text))
    # Replace the dates in the text
    dates = {key: config[key].get(day, '?') for key in ['time_open',
                                                        'time_close',
                                                        'time_force_menu',
                                                        'time_menu_close']}
    content = Template(content.safe_substitute(**dates))
    print(str2htmlascii(content.safe_substitute()))

    # Hide Seats if reservation is closed
    print('<script type="text/javascript">showhide('
          '\'wrapper_reservation\');</script>')
except:                                # pylint: disable=broad-except
    exc = traceback.format_exc()
    logging.critical(exc)
    print('<section>{}</section>'.format(error_to_html(exc)))
