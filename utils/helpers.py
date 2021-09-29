"""Helper functions for sitzreservation
"""
import os
import logging
import random
import traceback
if __name__ != "__main__":
    from .html import str2ascii
import hashlib
import pathlib

import pyqrcode
from PIL import Image
import base64

def create_bill_number(name, day):
    """Create a unique bill number.

    This is of the form SA1-EUG-012

    Arguments:
        name (str): Last name of the person.
        day (str): Day of the event
    """
    # a = seat.split('_')
    # p1 = a[0]+'%02d'%(int(a[1]))

    # Get the next higher 3 digit number.
    try:
        with open('data/numeration.txt', 'r+', encoding="utf-8") as f:
            current_n = int(f.read())
            f.seek(0)
            f.write(str(current_n + 1))
        count = '{:03}'.format(current_n)
    except Exception:
        logging.error('Could not retrieve bill number:\n%s',
                      traceback.format_exc())
        count = str(random.randint(600, 1000))

    # Get short name of the person
    short = str2ascii(name).upper()[:3]
    if len(short) < 3:
        short += 'X'*(3-len(short))

    return '%s-%s-%s'%(day, short, count)


def create_QR(file, data='nothing.'):
    
    # Generate the qr code and save as png
    qrobj = pyqrcode.create(data)

    # Create folders if they don't exist
    pathlib.Path(os.path.dirname(file)).mkdir(parents=True, exist_ok=True)     

    with open(file, 'wb') as f:
        #qrobj.png(f, scale=16)
        qrobj.png(f, scale=10)

    # Now open that png image to put the logo
    img = Image.open(file).convert("RGBA")
    width, height = img.size

    # How big the logo we want to put in the qr code png
    logo_size = 210 #368     # 16*23

    # Open the logo image
    logo = Image.open('img/TVM_logo.png')

    # Calculate xmin, ymin, xmax, ymax to put the logo
    xmin = ymin = int((width / 2) - (logo_size / 2))
    xmax = ymax = int((width / 2) + (logo_size / 2))

    # resize the logo as calculated
    logo = logo.resize((xmax - xmin, ymax - ymin))

    # put the logo in the qr code
    img.paste(logo, (xmin, ymin, xmax, ymax), logo)

    img.save(file)


def certificate(s):
    hasher = hashlib.sha256()
    hasher.update(s.encode('utf-8'))
    

    # len: 32 8-bit characters
    plain = int.from_bytes(hasher.digest(), 'big')
    
    
    # FIXME: private key
    p =         1408199503          # the primes p and q are not really
    q =          906199531          # needed to be part of the key
    w = 212684954476439010          # w = lcm(p-1, q-1)
    e =    120820088039939          # 1 < e < w, gcd(e, w) == 1

    # FIXME: public key
    n = 1276109729173033093
    d =  197116842892907279         # d = e^(-1) (mod w)

    #validate_key(p, q, n, w, e, d)
    x = pow(plain, e, n)
    crypted = base64.b64encode(x.to_bytes(x.bit_length()//8 +1, 'big')).decode('utf-8')
    
    return crypted
    
def verify(s, certificate):
    # FIXME: public key
    n = 1276109729173033093
    d =  197116842892907279

    hasher = hashlib.sha256()
    hasher.update(s.encode('utf-8'))
    expected = int.from_bytes(hasher.digest(), 'big') % n

    received = pow(int.from_bytes(base64.b64decode(certificate), 'big'), d, n)
    
    print('Expected vs. received: {} - {}'.format(expected, received))
    return expected == received

def validate_key(p, q, n, w, e, d):
    import numpy as np
    if p*q != n:
        print('pq != n')
    elif w != np.lcm(p-1, q-1):
        print('w != lcm')
    elif e*d % w != 1:
        print('ed != 1 (mod w)')
    else:
        print('key seems fine.')
    
    
if __name__ == '__main__':
    s =  """Seats: sasöldfjöadsf"""
    s2 = """Seats: sasöldfjöadsf"""
    
    m = certificate(s)
    print('The certificate is: {}'.format(m))
    
    print('Validation: {}'.format(verify(s2, m)))


