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
import dynamic_parts as dyn

print('Content-Type: text/html; charset=utf-8')    # HTML is following
print('')                                        # blank line, end of headers

try:
    log_setup.setup(logfile='log/sitzreservation.log', color=True,
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
    if submitted and day is None:
        day = form.getvalue('day_memory', None)
    submitted_data = {key: html2utf8(form.getvalue(key, '')).strip().replace(',','') for key in
                      ['title', 'firstname', 'lastname', 'street', 'street_nr',
                       'postcode', 'city', 'address_supplement_1',
                       'address_supplement_2', 'email', 'email_confirm',
                       'comment']}
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
               '_legend': ''
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
            _s += ('<button type="button" onclick="showhide('
                   '\'wrapper_reservation\')">${button_show_seats}</button>')
        elif not is_open:
            _s += '<p class="warn_date">${warning_reservation_not_open}</p>'
        dynamic['_status'] = _s

        # Action
        if submitted:
            dynamic['_bill'] = dyn.do_reservation(submitted_data, text,
                                                  force_menu,
                                                  is_menu_closed, data,
                                                  form, day, config, file)
            data = seat.get_seat_info(file)

        # create other dynamic parts

        dynamic['_pricelist'] = dyn.create_price_list(text)
        dynamic['_menulist'] = dyn.create_menu_list(text, day)
        dynamic['_legend'] = dyn.create_legend(is_closed)
        dynamic['_room'] = dyn.create_room(submitted_data['seats'], data, config)
        if not is_closed:
            dynamic['_room'] = ('<p class="instruction" id="no_gaps">'
                                '${info_no_gaps}</p><p class="instruction">$'
                                '{info_choose_seat}</p>' +
                                dynamic['_room'])


        if is_open and not is_closed:
            dynamic['_form'] = dyn.create_address_form(form, force_menu,
                                                       is_menu_closed)
            dynamic['_general_info'] = dyn.create_general_info(text,
                                                               force_menu,
                                                               is_menu_closed)


    # Finally we put everything together and create the html
    # ------------------------------------------------------
    with open('config/template.html', 'r') as f:
        content = Template(f.read())
    # First substitute the dynamic parts
    content = Template(content.safe_substitute(**dynamic))
    # Then plug in all the text
    content = Template(content.safe_substitute(**text))
    # Replace the dates in the text
    dates = {key: config[key].get(day, '?').split(',')[0] for key in
             ['time_open', 'time_close', 'time_force_menu', 'time_menu_close']}
    content = Template(content.safe_substitute(**dates))
    print(str2htmlascii(content.safe_substitute()))

    # Hide Seats if reservation is closed
    if day is not None and is_closed:
        print('<script type="text/javascript">showhide('
              '\'wrapper_reservation\');</script>')
except:                                # pylint: disable=broad-except
    exc = traceback.format_exc()
    logging.critical(exc)
    print('<section>{}</section>'.format(error_to_html(exc)))
