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
    if not submitted:
        out += '<p class="welcome">${welcome}</p>'
        out += '<p class="welcome_info">${welcome_info}</p>'
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
                if paid_claimed:
                    selected = ' disabled'
                    if seat_id in selected_seats:
                        paid_claimed += ' current'
                elif seat_id in selected_seats:
                    selected = ' checked'
                else:
                    selected = ''

                out += ('<input type="checkbox" name="seat" value="{id}" '
                        'id="seat_{id}" class="seat{paid_claimed}"{selected}/>'
                        '<label for="seat_{id}" class="tablerow_{0} '
                        'tablenr_{1} seat_{2}"></label>'.format(
                            letter, j, i, seat_nr, id=seat_id,
                            selected=selected,
                            paid_claimed=paid_claimed))
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
            # The next parts are for remembering selections
            # and checked checkboxes
            'user_conf_menu' : ' checked' if form.getvalue('menus_conf', None) == 'all' else '',
            'user_conditions' : ' checked' if form.getvalue('conditions', None) == 'agreed' else '',
            'user_title_mr': ' selected' if _title == 'mr' else '',
            'user_title_ms': ' selected' if _title == 'ms' else '',
            }
    user.update(form_dict)

    with open('config/template_contact.html', 'r') as f:
        out = Template(f.read())

    if force_menu:
        _sub = ('<i>${form_force_menu}</i></p>'
                '<p><input type="checkbox" name="menus_conf" '
                'value="all" class="checkbox" ${user_menu_conf}>'
                '<label for="menus_conf" '
                'class="checkbox"${user_conf_menu}>${form_menu_conf}'
                '</label></p>'
                '<input type="hidden" name="menus">')
    elif is_menu_closed:
        _sub = ('<i>${info_menu_closed}</i></p>'
                '<input type="hidden" name="menus" value="0" disabled>'
                '<input type="hidden" name="menus_conf" '
                'value="not_used">')
    else:
        _sub = ('<label class="address">${form_nr_menus}*:</label>'
                '<input type="text" name="menus" value="${menus}" '
                'class="address" id="input_menus"></p>'
                '<input type="hidden" name="menus_conf" '
                'value="not_used">')
    out = Template(out.safe_substitute(menu_selection=_sub))
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
    out = Template("""
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
                    ${green_seat}
                </tbody>
            </table>
        </div>""")
    if is_closed:
        out = out.safe_substitute(green_seat='')
    else:
        out = out.safe_substitute(
            green_seat='<tr><th><img src="img/seats/seat_green.png"></th>'
                       '<th>${seat_legend_yours}</th></tr>')

    return out


def do_reservation(submitted_data, text, force_menu, is_menu_closed, data, form, day, config, file):

    _s = ''
    fullname = submitted_data['firstname'] + ' ' + submitted_data['lastname']


    # Check that at least one seat has been selected
    is_valid = True

    if form.getvalue('conditions', None) != 'agreed':
        _s += '<p class="warning">${validation_no_confirmation}</p>'
        is_valid = False

    if not len(submitted_data['seats']):
        _s += '<p class="warning">${validation_no_seats}</p>'
        is_valid = False

    # Validate form input
    for field in ['title', 'firstname', 'lastname', 'street', 'postcode',
                  'city', 'email', 'email_confirm', 'phone']:
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
    if force_menu:
        # all with menu
        menus = len(submitted_data['seats'])
        if not form.getvalue('menus_conf', ''):
            logging.debug('%s did not check the menu confirmation box', fullname)
            _s += '<p class="warning">${validation_no_menu_conf}</p>'
            is_valid = False
    elif is_menu_closed:
        menus = 0
    else:
        try:
            menus = int(form.getvalue('menus', ''))
            # Maximal one menu per seat
            if menus > len(submitted_data['seats']):
                logging.debug('%s did enter too many menus', fullname)
                _s += '<p class="warning">${validation_too_many_menus}</p>'
                menus = len(submitted_data['seats'])
        except ValueError:
            logging.debug('%s did not specify how the number of menus', fullname)
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
                send_email(submitted_data['email'],
                           mail_header,
                           Template(text['mail_wrapper']).safe_substitute(
                                content=Template(mail_body).safe_substitute(
                                    tickets=ticket_html_mail)),
                           attachments=attachments)
            except Exception:
                logging.error('Could not send bill by email!')
                _s += '<p class="warning">${warning_no_mail}</p>'
                logging.debug(traceback.format_exc())
            else:
                logging.info('email sent.')
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
#                     try:
#                         logging.info('OP email sent.')
#                         send_email(config['mail_admin'], '', '')
#                     except Exception:
#                         logging.warning('Could not send mail to admin.')
    return _s

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
