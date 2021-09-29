import logging
import os
import re
from string import Template
from datetime import datetime
from utils import seat
from utils.mail import send_email
from utils.html import str2html, html2utf8, error_to_html
from utils.helpers import create_bill_number, create_QR, certificate
import time
import traceback

def create_day_selection(day, text, submitted, *args, **kwargs):
    # top of the page with day selection
    out = ''
    if day is None:
        out += '<div><p class="instruction">${choose_day}</p></div>'
    else:
        out += ('<div class="smaller"><p class="instruction">'
               '${choose_another_day}</p></div>')
    out += '<p>'

    # FIXME: not very elegant.
    if day is not None:
        out += '<input type="hidden" name="day_memory", value="{}">'.format(day)

    # Add the buttons to select the day
    for key, val in text['days'].items():
        out += ('<button name="day" value="{0}" type="submit"'
               ' formnovalidate{disable}>{1}</button>'.format(key, val,
               disable=(' disabled' if key == day else '')))
    out += '</p></div>'
    # Add day specific Information about times
    if day is not None:
        out += '<p class="info_eventkey"><strong>Event key: {}</strong><br></p>'.format(day)
        out += '<p class="info_date"><strong>{}</strong><br>{}</p>'.format(
            text['days'][day],
            text['day_description'].format(**text['times'][day]))
            
    return out


def create_room(selected_seats, data, config):

    out = ('<div id="room">'
           '<img src="img/cuisine.png" id="cuisine">'
           '<img src="img/stage.png" id="stage">'
           '<img src="img/entry.png" id="entry">')
    nr_tables = config['tables']
    for letter in nr_tables.keys():
        out += ('<img src="img/row_{0}.png" '
                'class="tablerow_{0} letter">'.format(letter))
        for j in range(*nr_tables[letter]):
            tbl_nr = j - nr_tables[letter][0]
            out += ('<img src="img/table_{}.png" class="tablerow_{} '
                    'tablenr_{}">'.format(tbl_nr, letter, j))

            for i in range(config['seats_per_table']):
                seat_nr = tbl_nr*config['seats_per_table'] + i +1
                seat_id = '{}{:02}'.format(letter, seat_nr)

                seat = data.get(seat_id, None)
                paid_claimed = ''
                if seat is not None:
                    if seat.paid:
                        paid_claimed += ' paid'
                    elif seat.claimed:
                        paid_claimed += ' claimed'

                # Parse non-string data
#                 if paid_claimed:
#                     if seat_id in selected_seats:
#                         paid_claimed += ' current'
#                 elif seat_id in selected_seats:
#                     selected = ' checked'
#                 else:
                selected = ''

                out += ('<input type="checkbox" name="seat" value="{id}" '
                        'id="seat_{id}" class="seat{paid_claimed}"{selected}/>'
                        '<label for="seat_{id}" class="tablerow_{0} '
                        'tablenr_{1} seat_{2}"></label>'.format(
                            letter, j, i, seat_nr, id=seat_id,
                            selected=selected,
                            paid_claimed=paid_claimed))
                
                # Name next to seat
                overdue = ''
                showinfo = ''
                seat_menu = ''
                seatinfo = ''
                if seat is not None:
                    seat_name = seat.lastname
                    if seat_name:
                        showinfo = 'showinfo'
                    else:
                        seat_name = '________'
                        
                    # Rechnungs-Datum older than 10 days
                    if (seat.claimed and not seat.paid and
                            (time.mktime(time.localtime()) -
                             time.mktime(time.strptime(
                                seat.date_reservation,
                                '%Y-%m-%d %H:%M:%S'))) > 864000):
                        overdue = 'overdue'
                    
                    if seat.with_menu:
                        seat_menu = 'with_menu'
                    
                    seatinfo = Template(
                        '${op_popup_bill} #${bill_nr}\n'
                        '${op_popup_menu}: ${nr_menus}\n'
                        '${firstname} ${lastname}\n'
                        '${street} ${street_nr}\n'
                        '${postcode} ${city}\n'
                        '${address_supplement_1}\n'
                        '${address_supplement_2}\n'
                        '${op_popup_email}: ${email}\n'
                        '${op_popup_phone}: ${phone}\n'
                        '${comment}\n'
                        '${op_popup_res_date}: \t${date_reservation}\n'
                        '${op_popup_bill_date}: \t${date_bill_sent}\n'
                        '${op_popup_paid_date}: \t${date_paid}').safe_substitute(**seat.info)
                    seatinfo = re.sub('(?:\\n)+','\\n', seatinfo)
                    
                    
                    ['number', 'claimed', 'paid', 'nr_menus',
                     'date_reservation', 'date_paid', 'date_bill_sent',
                     'bill_nr', 'title', 'firstname', 'lastname',
                     'street', 'street_nr', 'postcode', 'city',
                     'address_supplement_1', 'address_supplement_2',
                     'email', 'phone', 'comment']
                    
                else:
                    seat_name = '________'

                
                
                out += ('<p class="seatname tablerow_{1} tablenr_{2} '
                        'seat_{3} {4} {5} {6}" '
                        'title="{7}">{0}</p>'.format(
                            seat_name, letter, j, i, overdue, seat_menu,
                            showinfo, seatinfo))

    
    
    
    out += '</div>'
    return out


def create_address_form(form, force_menu, is_menu_closed):
    form_dict = {key: form.getvalue(key) for key in form.keys()}
    _title = form.getvalue('title', None)
    user = {'street': '',
            'firstname': '',
            'lastname': '',
            'street': '',
            'street_nr': '',
            'postcode': '',
            'city': '',
            'address_supplement_1': '',
            'address_supplement_2': '',
            'email': '',
            'email_confirm': '',
            'phone': '',
            'comment': '',
            'menus': '',
            'user_send_email': ' checked' if form.getvalue('send_email', None) == 'send' else '',
            # The next parts are for remembering selections
            # and checked checkboxes
            'user_conf_menu' : ' checked' if form.getvalue('menus_conf', None) == 'all' else '',
            'user_conditions' : ' checked' if form.getvalue('conditions', None) == 'agreed' else '',
            'user_title_mr': ' selected' if _title == 'mr' else '',
            'user_title_ms': ' selected' if _title == 'ms' else '',
            }
    user.update(form_dict)

    with open('config/template_contact_op.html', 'r') as f:
        out = Template(f.read())


    _sub = ('<label class="address">${form_nr_menus}*:</label>'
            '<input type="text" name="menus" value="${menus}" '
            'class="address" id="input_menus"></p>'
            '<input type="hidden" name="menus_conf" '
            'value="not_used">')
    
    
    out = Template('<button onclick="showhide(\'wrapper_contact\')" type="button">${op_show_contact}</button>'
                   '<div id="wrapper_contact" style="display:none;">' +
                   out.safe_substitute(menu_selection=_sub) +
                   '</div>')
    return out.safe_substitute(**user)


def create_general_info(text, force_menu, is_menu_closed):
    # Put a small number in front of each line.
    numbers = ['&#x00B9;', '&#x00B2;', '&#x00B3;', '&#x2074;',
               '&#x2075;', '&#x2076;', '&#x2077;', '&#x2078;',
               '&#x2079;']
    _lines = re.split('<br>' ,text['general_info'])
    out = Template('<br>'.join(numbers[i] + _lines[i]
                               for i, line in enumerate(_lines)))

    # Text variations depending of status of buying menus
    if force_menu:
        _info = text['info_menu_only']
    elif is_menu_closed:
        _info = text['info_menu_closed']
    else:
        _info = text['info_menu_open']
    out = out.safe_substitute(info_about_menu=_info)
    # Put it into html
    out = ('<div id="info">'
           '<h3 class="information">Infos</h3>'
           '<p class="information">{}</p>'
           '</div>'.format(out))
    return out


def create_price_list(text):

    out = ('<div><table>'
           '<caption>${caption_price_list}</caption><tbody>')

    for prc, txt in zip(text['prices'], text['prices_text']):
        out += '<tr><th>{} {}</th><th>{}</th></tr>'.format(prc,
                                                           text['currency'],
                                                           txt)
    out += ('</tbody></table></div>')
    return out


def create_menu_list(text, day):

    out = ('<div><table>'
           '<caption>${caption_menu_list}</caption><tbody>')
    for m in text['menu'][day]:
        out += '<tr><th>{}</th></tr>'.format(m)
    out += ('</tbody></table></div>')
    return out


def create_legend(is_closed):
    out = """
        <div>
            <table>
                <caption>${caption_seat_legend}</caption>
                <tbody>
                    <tr><th><img src="img/seats/seat_white.png"></th>
                        <th>${seat_legend_free}</th></tr>
                    <tr><th><img src="img/seats/seat_yellow.png"></th>
                        <th>${seat_legend_occupied}</th></tr>
                    <tr><th><img src="img/seats/seat_red.png"></th>
                        <th>${seat_legend_paid}</th></tr>
                    <tr><th class="with_menu"></th>
                        <th>${op_legend_with_menu}</th></tr>
                    <tr><th class="overdue"></th>
                        <th>${op_legend_overdue}</th></tr>
                </tbody>
            </table>
        </div>"""

    return out


def do_reservation(submitted_data, text, force_menu, is_menu_closed, data, form, day, config, file):

    _s = ''
    fullname = (submitted_data.get('firstname', '') + ' ' + submitted_data['lastname']).strip()


    # Check that at least one seat has been selected
    is_valid = True

#     if form.getvalue('conditions', None) != 'agreed':
#         _s += '<p class="warning">${validation_no_confirmation}</p>'
#         is_valid = False

    if not len(submitted_data['seats']):
        _s += '<p class="warning">${validation_no_seats}</p>'
        is_valid = False

    # Validate form input
    for field in ['lastname']:
        if submitted_data[field] == '':
            logging.debug('%s did not fill out all fields', fullname)
            _lookup = {'title': text['form_title'],
                       'firstname': text['form_firstname'],
                       'lastname': text['form_lastname'],
                       'street': text['form_street'],
                       'postcode': text['form_postcode'],
                       'city': text['form_city'],
                       'email': text['form_email'],
                       'email_confirm': text['form_email'],
                       'phone': text['form_phone']}
            _s += '<p class="warning">{}</p>'.format(Template(
                text['validation_required_fields']).safe_substitute(
                    missing_field=_lookup.get(field, '')))
            is_valid = False
    if submitted_data['email'] != submitted_data['email_confirm']:
        logging.debug('%s misspelled their email', fullname)
        _s += '<p class="warning">${warning_emails_dont_match}</p>'
        is_valid = False

    # Check if seats are still free
    occupied = []
    for st in submitted_data['seats']:
        if st in data and (data[st].claimed or data[st].paid):
            occupied.append(st)
    if occupied:
        logging.debug('%s selected occupied seats (%s)', fullname, ', '.join(occupied))
        _s += ('<p class="warning">${warning_occupied_seat}<br>'
               '%s</p>' % (', '.join(occupied)))
        is_valid = False

    # Validate menus
#     if force_menu:
#         # all with menu
#         menus = len(submitted_data['seats'])
#         if not form.getvalue('menus_conf', ''):
#             logging.debug('%s did not check the menu confirmation box', fullname)
#             _s += '<p class="warning">${validation_no_menu_conf}</p>'
#             is_valid = False
#     elif is_menu_closed:
#         menus = 0
#     else:
    try:
        menus = int(form.getvalue('menus', ''))
        # Maximal one menu per seat
        if menus > len(submitted_data['seats']):
            logging.debug('%s did enter too many menus', fullname)
            _s += '<p class="warning">${validation_too_many_menus}</p>'
            menus = len(submitted_data['seats'])
    except ValueError:
        logging.debug('%s did not specify the number of menus', fullname)
        _s += '<p class="warning">${validation_no_menus}</p>'
        is_valid = False
    logging.debug("%s's reservation is valid: %s", fullname, is_valid)

    # Do the reservation, send emails and print bill
    if is_valid:
        bill_nr = create_bill_number(submitted_data['lastname']+submitted_data['firstname'], day)

        changes = {}
        for i, nr in enumerate(submitted_data['seats']):
            info = {'number': nr,
                    'claimed': True,
                    'paid': False,
                    'nr_menus': int(i<menus),
                    'date_reservation': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'date_bill_sent': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'bill_nr': bill_nr}
            changes[nr] = seat.Seat(**info, **submitted_data)
        logging.info('%s made a reservation with nr. %s \n(%s)',
                     fullname,
                     bill_nr,
                     '\n '.join(map(str, changes)))

        failed = apply_changes(changes, config['files'][day], fullname)
        logging.info('Saved data for %s', bill_nr)

        # Send mail to admin if data is locked
        if failed == 'file_occupied':
            logging.error('%s failed to do a reservation due to '
                          'a lockfile!', fullname)
            _s += '<p class="warning">${error_lockfile}</p>'
            send_email(config['mail_admin'],
                       text['mail_subj_lockfile'],
                       text['mail_lockfile'])

        if failed:
            _s += '<p class="warning">${reservation_unsuccessful}</p>' #TODO
            logging.warning('Reservation not successful!')
        else:
            data = seat.get_seat_info(file)
            _s += '<p class="info_successful">${reservation_successful}</p>'

            # Display the address to the user
            address = [' ' + submitted_data['firstname'] + ' ' + submitted_data['lastname'],
                       submitted_data['street'] + ' ' + submitted_data['street_nr'],
                       submitted_data['address_supplement_1'],
                       submitted_data['address_supplement_2'],
                       submitted_data['postcode'] + ' ' + submitted_data['city'],
                       submitted_data['email'],
                       submitted_data['phone']]
            address = [s for s in address if s] # remove empty lines
            address = ('<br>' + '&nbsp;'*4).join(['', *address])
            _s += Template('<p class="info_address">${info_your_address}${address}</p>').safe_substitute(address=address)

            ticket_html = ''
            ticket_html_mail = ''
            attachments = {}
            
            
            _is_mr = (submitted_data['title'] == 'mr')
            if menus == 0:
                text_menus = text['no_menu']
            elif menus == 1:
                text_menus = text['one_menu']
            else:
                text_menus = text['more_menu']
            text_menus = Template(text_menus).safe_substitute(n=menus)
            mail_header = html2utf8(Template(text['mail_sbj_bill']).safe_substitute(day=text['days'][day], bill_nr=bill_nr))



            # QR code
            submitted_data['seats'] = sorted(submitted_data['seats'])
            qr_code = 'tmp/qr/{}.png'.format(bill_nr)

            qr_data = Template('${qr_title}\n${qr_nr} ${value_nr}\n'
                               '${qr_seat}: ${value_seat}\n'
                               '${qr_menu}: ${value_menu}\n'
                               ).safe_substitute(
                value_nr=bill_nr,
                value_seat=', '.join(submitted_data['seats']),
                value_menu=menus,
                qr_title = text['qr_title'],
                qr_seat = text['qr_seat'],
                qr_menu = text['qr_menu'],
                qr_nr = text['qr_nr'])
            
            # Use RSA to create checksum
            qr_data = Template(
                qr_data + '${qr_checksum}: ${value_checksum}').safe_substitute(
                value_checksum=certificate(qr_data),
                qr_checksum = text['qr_checksum'])        
                            
            create_QR(file=qr_code,
                      data=qr_data)
            attachments['qr_code_0'] = os.path.abspath(qr_code)
            ticket_html += Template(text['mail_ticket_template']).safe_substitute(
                css_class='ticket_all_seats',
                qr_code=qr_code,
                quantifier=text['mail_word_all'],
                seats=', '.join(submitted_data['seats']),
                event='{} {}'.format(text['days'][day], text['times'][day]['time_start']),
                menu='({})'.format(text_menus.strip('()')),
                year=text['year'])
            ticket_html_mail += Template(text['mail_ticket_template']).safe_substitute(
                css_class='ticket_all_seats',
                qr_code='cid:qr_code_0',
                quantifier=text['mail_word_all'],
                seats=', '.join(submitted_data['seats']),
                event='{} {}'.format(text['days'][day], text['times'][day]['time_start']),
                menu='({})'.format(text_menus.strip('()')),
                year=text['year'])
                
            if len(submitted_data['seats']) > 1:
                for i, s in enumerate(submitted_data['seats']):
                    _qr_code = 'tmp/qr/{}_{}.png'.format(bill_nr, i+1)

                    _qr_data = Template('${qr_title}\n${qr_nr} ${value_nr}\n'
                                        '${qr_seat}: ${value_seat}\n'
                                        '${qr_menu}: ${value_menu}\n'
                                        ).safe_substitute(
                        value_nr=bill_nr,
                        value_seat=s,
                        value_menu=int(i<menus),
                        qr_title = text['qr_title'],
                        qr_seat = text['qr_seat'],
                        qr_menu = text['qr_menu'],
                        qr_nr = text['qr_nr'])
            
                    # Use RSA to create checksum
                    _qr_data = Template(_qr_data +
                        '${qr_checksum}: ${value_checksum}').safe_substitute(
                            value_checksum=certificate(_qr_data),
                            qr_checksum = text['qr_checksum'])        
                            
                    create_QR(file=_qr_code,
                              data=_qr_data)
                    attachments['qr_code_{}'.format(i+1)] = os.path.abspath(_qr_code)
                    ticket_html += Template(text['mail_ticket_template']).safe_substitute(
                        css_class='',
                        qr_code=_qr_code,
                        quantifier=text['mail_word_single'],
                        seats=s,
                        menu= '({})'.format(text['mail_single_with_menu']) if i < menus else '',
                        event='{} {}'.format(text['days'][day], text['times'][day]['time_start']),
                        year=text['year'])
                    ticket_html_mail += Template(text['mail_ticket_template']).safe_substitute(
                        css_class='',
                        qr_code='cid:qr_code_{}'.format(i+1),
                        quantifier=text['mail_word_single'],
                        seats=s,
                        menu= '({})'.format(text['mail_single_with_menu']) if i < menus else '',
                        event='{} {}'.format(text['days'][day], text['times'][day]['time_start']),
                        year=text['year'])
                    

            # Send mail with bill            
            mail_body = Template(text['mail_msg_bill']).safe_substitute(
                name=submitted_data['firstname'] + ' ' + submitted_data['lastname'],
                title=text['form_title_mr'] if _is_mr else text['form_title_ms'],
                r='r' if _is_mr else '',
                seats=', '.join(submitted_data['seats']),
                n='n' if len(submitted_data['seats']) == 1 else '',
                e='' if len(submitted_data['seats']) == 1 else 'e',
                bill_nr=bill_nr,
                price_seat=text['prices'][0],
                price_menu=text['prices'][1],
                nr_seats=len(submitted_data['seats']),
                nr_menus=menus,
                costs_seats=text['prices'][0]*len(submitted_data['seats']),
                costs_menu=text['prices'][1]*menus,
                costs_total=text['prices'][0]*len(submitted_data['seats']) + text['prices'][1]*menus,
                s='' if menus == 1 else 's',
                menus=text_menus,
                day=text['days'][day],
                year=text['year'])
            try:
                if submitted_data.get('send_email', None):
                    send_email(submitted_data['email'],
                               mail_header,
                               Template(text['mail_wrapper']).safe_substitute(
                                    content=Template(mail_body).safe_substitute(
                                        tickets=ticket_html_mail)),
                               attachments=attachments)
                    logging.info('email sent.')
            except Exception:
                logging.error('Could not send bill by email!')
                _s += '<p class="warning">${warning_no_mail}</p>'
                logging.debug(traceback.format_exc())
            else:
                _s += '<p class="information">{}</p>'.format(
                    Template(text['info_bill_sent']).safe_substitute(
                        email=submitted_data['email']))
                _s += '<p class="warning">${warning_format_error_outlook}</p>'


            # Display bill
            _s += '<button onclick="showhide(\'bill\')" type="button">${show_bill}</button>'
            _s += '<div id="bill">'
            _s += '<button id="print_button" onclick="printDiv(\'bill\')" type="button">${print_bill}</button>'
            _s += Template('<h4>${title_billnr} ${bill_nr}</h4>').safe_substitute(bill_nr=bill_nr)
            _s += '<p class="confirmation">{}</p></div>'.format(
                Template(mail_body).safe_substitute(
                    tickets=ticket_html))

            # Send mail to OPs and admins
            try:
                logging.info('OP email sent.')
                for address in config['mail_op']:
                    send_email(address,
                               text['word_copy'] + ': ' + mail_header,
                               Template(text['mail_wrapper']).safe_substitute(
                                    content=Template(mail_body).safe_substitute(
                                        tickets=ticket_html_mail)),
                               attachments=attachments)
            except Exception:
                logging.warning('Could not send mail to OP.')
                logging.warning(traceback.format_exc())
#                     try:
#                         logging.info('OP email sent.')
#                         send_email(config['mail_admin'], '', '')
#                     except Exception:
#                         logging.warning('Could not send mail to admin.')
    return _s


def resend_email(bill_nr, submitted_data, text, day):
    submitted_data['seats'] = sorted(submitted_data['seats'])
    
    out = ''
    
    ticket_html_mail = ''
    attachments = {}
    
    
    _is_mr = (submitted_data['title'] == 'mr')
    menus = submitted_data['menus']
    if menus == 0:
        text_menus = text['no_menu']
    elif menus == 1:
        text_menus = text['one_menu']
    else:
        text_menus = text['more_menu']
    text_menus = Template(text_menus).safe_substitute(n=menus)
    mail_header = html2utf8(Template(text['mail_sbj_bill']).safe_substitute(day=text['days'][day], bill_nr=bill_nr))



    # QR code
    submitted_data['seats'] = sorted(submitted_data['seats'])
    qr_code = 'tmp/qr/{}.png'.format(bill_nr)

    qr_data = Template('${qr_title}\n${qr_nr} ${value_nr}\n'
                       '${qr_seat}: ${value_seat}\n'
                       '${qr_menu}: ${value_menu}\n'
                       ).safe_substitute(
        value_nr=bill_nr,
        value_seat=', '.join(submitted_data['seats']),
        value_menu=menus,
        qr_title = text['qr_title'],
        qr_seat = text['qr_seat'],
        qr_menu = text['qr_menu'],
        qr_nr = text['qr_nr'])
    
    # Use RSA to create checksum
    qr_data = Template(
        qr_data + '${qr_checksum}: ${value_checksum}').safe_substitute(
        value_checksum=certificate(qr_data),
        qr_checksum = text['qr_checksum'])        
                    
    create_QR(file=qr_code,
              data=qr_data)
    attachments['qr_code_0'] = os.path.abspath(qr_code)
    ticket_html_mail += Template(text['mail_ticket_template']).safe_substitute(
        css_class='ticket_all_seats',
        qr_code='cid:qr_code_0',
        quantifier=text['mail_word_all'],
        seats=', '.join(submitted_data['seats']),
        event='{} {}'.format(text['days'][day], text['times'][day]['time_start']),
        menu='({})'.format(text_menus),
        year=text['year'])
        
    if len(submitted_data['seats']) > 1:
        for i, s in enumerate(submitted_data['seats']):
            _qr_code = 'tmp/qr/{}_{}.png'.format(bill_nr, i+1)

            _qr_data = Template('${qr_title}\n${qr_nr} ${value_nr}\n'
                                '${qr_seat}: ${value_seat}\n'
                                '${qr_menu}: ${value_menu}\n'
                                ).safe_substitute(
                value_nr=bill_nr,
                value_seat=s,
                value_menu=int(i<menus),
                qr_title = text['qr_title'],
                qr_seat = text['qr_seat'],
                qr_menu = text['qr_menu'],
                qr_nr = text['qr_nr'])
    
            # Use RSA to create checksum
            _qr_data = Template(_qr_data +
                '${qr_checksum}: ${value_checksum}').safe_substitute(
                    value_checksum=certificate(_qr_data),
                    qr_checksum = text['qr_checksum'])        
                    
            create_QR(file=_qr_code,
                      data=_qr_data)
            attachments['qr_code_{}'.format(i+1)] = os.path.abspath(_qr_code)
            ticket_html_mail += Template(text['mail_ticket_template']).safe_substitute(
                css_class='',
                qr_code='cid:qr_code_{}'.format(i+1),
                quantifier=text['mail_word_single'],
                seats=s,
                menu= '({})'.format(text['mail_single_with_menu']) if i < menus else '',
                event='{} {}'.format(text['days'][day], text['times'][day]['time_start'],
                year=text['year']))
            

    # Send mail with bill            
    mail_body = Template(text['mail_msg_bill']).safe_substitute(
        name=submitted_data['firstname'] + ' ' + submitted_data['lastname'],
        title=text['form_title_mr'] if _is_mr else text['form_title_ms'],
        r='r' if _is_mr else '',
        seats=', '.join(submitted_data['seats']),
        n='n' if len(submitted_data['seats']) == 1 else '',
        e='' if len(submitted_data['seats']) == 1 else 'e',
        bill_nr=bill_nr,
        price_seat=text['prices'][0],
        price_menu=text['prices'][1],
        nr_seats=len(submitted_data['seats']),
        nr_menus=menus,
        costs_seats=text['prices'][0]*len(submitted_data['seats']),
        costs_menu=text['prices'][1]*menus,
        costs_total=text['prices'][0]*len(submitted_data['seats']) + text['prices'][1]*menus,
        s='' if menus == 1 else 's',
        menus=text_menus,
        day=text['days'][day],
        year=text['year'])
    try:
        send_email(submitted_data['email'],
                   mail_header,
                   Template(text['mail_wrapper']).safe_substitute(
                        content=Template(mail_body).safe_substitute(
                            tickets=ticket_html_mail)),
                   attachments=attachments)
    except Exception:
        logging.error('Could not send bill by email!')
        out += '<p class="warning">${warning_no_mail}</p>'
        logging.debug(traceback.format_exc())
    else:
        logging.info('email sent.')
        out += '<p class="information">{}</p>'.format(
            Template(text['info_bill_sent']).safe_substitute(
                email=submitted_data['email']))
    return out


def apply_changes(changes, file, fullname): 
    failed = True
    for i in [0, 0.02, .05, .1, .2, .4, .8, 1.6, 3.2]:
        time.sleep(i)
        failed = seat.write_data(changes=changes, file=file, allowEdit=True)

        if failed:
            # file occupied or seats already selected
            if failed == 'file_occupied':
                continue
            logging.warning('%s tried to get occupied seats', fullname)
            selected_seats = []
        break
    return failed


def free_seat(seats, data):
    changes = dict()
    for i, nr in enumerate(seats):
        if nr in data and data[nr].paid:
            return None, '<p class="warning">${op_warning_cant_free}</p>'
        
        info = {'number': nr,
                'claimed': False,
                'paid': False,
                'nr_menus': 0,
                'date_reservation': '',
                'date_paid': '',
                'date_bill_sent': '',
                'bill_nr': '',
                'title': '',
                'firstname': '',
                'lastname': '',
                'street': '',
                'street_nr': '',
                'postcode': '',
                'city': '',
                'address_supplement_1': '',
                'address_supplement_2': '',
                'email': '',
                'phone': '',
                'comment': ''}
        changes[nr] = seat.Seat(**info)
        
    logging.info('OP freed the seats %s', seats)
    return changes, ''


def seat_paid(seats, data):
    out = ''
    changes = dict()
    already_paid = []
    not_claimed = []
    for i, nr in enumerate(seats):
        if nr in data and data[nr].paid:
            already_paid.append(nr)
        if nr not in data or not data[nr].claimed:
            not_claimed.append(nr)
        
        info = {'number': nr,
                'paid': True}
        changes[nr] = seat.Seat(**info)
     
    _valid = True   
    if already_paid:
        out += ('<p class="warning">${op_warning_already_paid}: ' +
                ', '.join(already_paid) + '</p>')
        _valid = False
    if not_claimed:
        out += ('<p class="warning">${op_warning_not_claimed}: ' +
                ', '.join(not_claimed) + '</p>')
        _valid = False
        
    if not _valid:
        return None, out
    logging.info('OP confirmed payment for the seats %s.', seats)
    return changes, out


def delete_payment(seats, data):
    changes = dict()
    not_paid = []
    for i, nr in enumerate(seats):
        if nr in data and not data[nr].paid:
            not_paid.append(nr)
        info = {'number': nr,
                'paid': False}
        changes[nr] = seat.Seat(**info)
    
    if not_paid:
        return None, ('<p class="warning">${op_warning_not_paid}' +
                      ', '.join(not_paid) + '</p>')
        
    logging.info('OP deleted payment for the seats %s.', seats)
    return changes, ''


def resend_bill(seats, data, day, text):
    out = ''
    reminders = dict()
    menus = dict()
    changes = dict()
    for i, nr in enumerate(seats):
        if nr in data and not data[nr].paid:
            bill_nr = data[nr].bill_nr
            if bill_nr is None:
                continue
            
            if bill_nr in reminders:
                reminders[bill_nr]['seats'].append(nr)
                reminders[bill_nr]['menus'] += data[nr].menu
                
            else:
                user_data = {'firstname': data[nr].firstname,
                             'lastname': data[nr].lastname,
                             'seats': [nr],
                             'email': data[nr].email,
                             'menus': data[nr].menu,
                             'title': data[nr].title}
                reminders[bill_nr]  = user_data
            
            info = {'number': nr,
                    'date_bill_sent': datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            changes[nr] = seat.Seat(**info)

            
    for bill_nr, user_data in reminders.items():
        out += resend_email(bill_nr, user_data, text, day)
    
    return changes, out
 
 
def create_stats(data, config):
    STAT_tot = 0
    for _, r in config['tables'].items():
        STAT_tot += r[1] - r[0]
    STAT_tot *= config['seats_per_table']
    
    
    now = time.mktime(time.localtime())
    STAT_paid = 0
    STAT_res = 0
    STAT_menu = 0
    STAT_overdue = set()
    for nr, seat in data.items():
        if seat.claimed:
            STAT_res += 1
        if seat.paid:
            STAT_paid += 1
        STAT_menu += seat.menu
        if (seat.claimed and not seat.paid and
                (now - time.mktime(time.strptime(
                                   seat.date_reservation,
                                   '%Y-%m-%d %H:%M:%S'))) > 864000):
            STAT_overdue.add(seat.bill_nr)
   
    
    if len(STAT_overdue) != 0:
        if False: #FIXME #len(STAT_overdue) > 4:
            float_box = ('<div id="overdue_nr"><strong>${stat_overdue}:'
                         '</strong><br>' +
                         ',<br>'.join(sorted(STAT_overdue)[0:4]) +
                         '<br>...</div>'
                         )
        else:
            float_box = ('<div id="overdue_nr"><strong>${stat_overdue}:'
                         '</strong><br>' +
                         ',<br>'.join(sorted(STAT_overdue)) +
                         '</div>')
    else:
       float_box = '' 

    out = Template("""
        <div id="statistics">
            ${float_box}
            <p class="instruction">${stat_statistics}:</p>
            <table><tbody>
                <tr><th>${stat_menu}</th><th>${STAT_menu}</th><th></th></tr>
                <tr>
                    <th>${stat_claimed_seats}</th>
                    <th>${STAT_res}</th><th>${stat_of} ${STAT_tot}</th>
                </tr>
                <tr>
                    <th>${stat_paid}</th><th>${STAT_paid}</th>
                    <th>${stat_of} ${STAT_res}</th>
                </tr>
                <tr>
                    <th>${stat_free_seats}</th>
                    <th>${STAT_diff}</th>
                    <th></th>
                </tr>
                <tr>
                    <th>${stat_overdue_bill}</th>
                    <th>${no_overdue}</th>
                    <th></th>
                </tr>
            </table></tbody>
        </div>
    """).safe_substitute(float_box=float_box,
                         STAT_menu=STAT_menu,
                         STAT_res=STAT_res,
                         STAT_tot=STAT_tot,
                         STAT_paid=STAT_paid,
                         STAT_diff=STAT_tot-STAT_res,
                         no_overdue=len(STAT_overdue))
        

    return out