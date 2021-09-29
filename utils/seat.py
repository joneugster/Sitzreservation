#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Module for managing teh Seats

We represent a seats with a class and provide writing and reading
methods so that it would be easier to change later to a proper
data base.
"""
# pylint: disable=invalid-name
import os
import re

SEP = ','


def create_file(file='data/data.csv', columns=None):
    """Create a data file and adjust permissions."""
    if columns is None:
        columns = []

    path = os.path.dirname(file)
    os.system('chmod a+w {}'.format(path))

    with open(file, 'w') as f:
        f.write(SEP.join(columns) + '\n')

    os.system('chmod a+w {}'.format(file))


def write_data(changes=None, file='data/data.csv', allowEdit=False):
    """Write seats to data file.

    Returns:
        (str/None):
            None: Successful
            'file_occupied': File locked
            'failed': Seat already occupied
    """
    # Create a lockfile to prevent simultaneous writing
    path = os.path.dirname(file)
    filename = os.path.splitext(os.path.basename(file))[0]
    lockfile = os.path.join(path, 'lockfile_{}'.format(filename))

    if os.path.exists(lockfile):
        return 'file_occupied'

    os.system('touch %s'%lockfile)

    out = ''
    with open(file, 'r+', encoding="utf-8") as f:
        for i, line in enumerate(f):
            # Skip the header
            if i == 0:
                out += line
                continue

            # Read data
            data = [x.strip() for x in
                    re.split(r'\s*{}\s*'.format(SEP), line)]
            nr = data[0]
            new = Seat(*data)
            # Update the seat
            iter_list= changes.keys()
            if nr in iter_list:
                x = changes.pop(nr)
                if not allowEdit and (new.paid or new.claimed):
                    return 'failed'
                new.update(x)
                out += repr(new) + '\n'
            else:
                out += line

        # Add all new seats
        for nr, chg in changes.items():
            out += repr(chg) + '\n'

        # Write everything back into the file
        f.seek(0)
        f.write(out)
        f.truncate()

    #remove lockfile
    os.system('rm {}'.format(lockfile))
    return None

def get_seat_info(file='data/data.csv'):
    """Read the seat info from the file."""
    with open(file, 'r', encoding="utf-8") as f:
        out = {}
        for i, line in enumerate(f):
            # Skip the header
            if i == 0:
                continue

            # Read data
            data = [x.strip() for x in
                    re.split(r'\s*{}\s*'.format(SEP), line)]
            nr = data[0]
            out[nr] = Seat(*data)

    return out



class Seat:
    """Representing a seat.

    You can use repr(seat) to create a line you can put into a CSV file.
    """

    def __init__(self, *data, **info):
        """
        Can be either constructed by a list or a dictionary

        Arguments:
            number (str): seat number (e.g. 'E_15')
            *data:
                number (str)
                claimed (bool)
                paid (bool)
                no_of_menus (int)
                date_reservation ()
                date_paid ()
                date_bill_sent ()
                bill_nr (str)
                title (str)
                name (str)
                street (str)
                city (str)
                address_supplement_1 (str)
                address_supplement_2 (str)
                email (str)
                phone (str)
                comment (str)

            **info:
                number (str)
                claimed (bool)
                paid (bool)
                no_of_menus (int)
                date_reservation ()
                date_paid ()
                date_bill_sent ()
                bill_nr (str)
                title (str)
                name (str)
                street (str)
                city (str)
                address_supplement_1 (str)
                address_supplement_2 (str)
                email (str)
                phone (str)
                comment (str)
        """
        self.keys = ['number', 'claimed', 'paid', 'nr_menus',
                     'date_reservation', 'date_paid', 'date_bill_sent',
                     'bill_nr', 'title', 'firstname', 'lastname',
                     'street', 'street_nr', 'postcode', 'city',
                     'address_supplement_1', 'address_supplement_2',
                     'email', 'phone', 'comment']


        #self.info = {key: '' for key in self.keys}
        #self.info['claimed'] = False
        #self.info['paid'] = False
        #self.info['nr_menus']: 0
        #self.info_new = info

        if data:
            try:
                self.info = {self.keys[i]: val for i, val in enumerate(data)}
            except IndexError:
                print('{}<br>'.format(data))
            if isinstance(self.paid, str):
                self.info['paid'] = self.info['paid'].lower() == 'true'
            if isinstance(self.claimed, str):
                self.info['claimed'] = self.info['claimed'].lower() == 'true'
            if isinstance(self.info.get('nr_menus', 0), str):
                self.info['nr_menus'] = int(self.info['nr_menus'])
        else:
            self.info = info

    def __repr__(self):
        out = {key:'' for key in self.keys}
        out.update(self.info)
        return '{sep}'.join('{%s}' % key for key in
                            self.keys).format(sep=SEP, **out)

    @property
    def paid(self):
        """has the seat been paid."""
        return self.info.get('paid', False)

    @property
    def bill_nr(self):
        """"""
        return self.info.get('bill_nr', None)

    @property
    def lastname(self):
        """"""
        return self.info.get('lastname', 'unknown')

    @property
    def firstname(self):
        """"""
        return self.info.get('firstname', '')

    @property
    def email(self):
        """"""
        return self.info.get('email', '')

    @property
    def claimed(self):
        """has the seat been reserved."""
        return self.info.get('claimed', False)

    @property
    def with_menu(self):
        """does the seat come with menu."""
        return self.info.get('nr_menus', 0) > 0
    @property
    def menu(self):
        """does the seat come with menu."""
        return self.info.get('nr_menus', 0)

    @property
    def title(self):
        """"""
        return self.info.get('title', '')

    @property
    def date_reservation(self):
        """has the seat been reserved."""
        return self.info.get('date_reservation', '1990-01-01 00:00:00')


    def update(self, other):
        """update the seat with new data."""
        self.info.update(other.info)
