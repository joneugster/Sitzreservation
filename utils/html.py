"""String convertion functions to work with HTML."""
import re


def str2html(text):
    """Escape UTF8 string with HTML syntax."""
    if isinstance(text, str):
        out = ''
        for char in text:
            # &, < and >
            if ord(char) in [38, 60, 62] or ord(char) > 127:
                out += '&#%d;' % (ord(char))
            elif ord(char) == 10:
                out += '<br>'
            elif ord(char) == 9:
                out += '&nbsp;'*4
            else:
                out += char
        return out
    if text is None:
        return ''
    raise TypeError('str2html() expects a string!')


def html2utf8(text):
    """Convert HTML escape sequences to UTF8 characters."""
    if isinstance(text, str):
        text = re.sub('&#([0-9]+);?', lambda mch: chr(int(mch.group(1))), text)
        return text
    if text is None:
        return ''
    raise TypeError('html2utf8() expects a string!')


def str2htmlascii(text):
    if isinstance(text, str):
        out = ''
        for char in text:
            if ord(char) > 127:
                out += '&#%d;' % (ord(char))
            else:
                out += char
        return out
    if text is None:
        return ''
    raise TypeError('str2html() expects a string!')

def str2ascii(text):
    """Convert UTF8 string to ASCII."""
    repl_dict = {'ä':'ae', 'Ä':'Ae', 'à':'a', 'À':'A', 'â':'a', 'Â':'A',
                 'ë':'e', 'Ë':'E', 'è':'e', 'È':'E', 'ê':'e', 'Ê':'E',
                 'é':'e', 'É':'E',
                 'ï':'i', 'Ï':'I', 'ì':'i', 'Ì':'I', 'î':'i', 'Î':'I',
                 'ö':'oe', 'Ö':'Oe', 'ò':'o', 'Ò':'O', 'ô':'o', 'Ô':'O',
                 'ü':'ue', 'Ü':'Ue', 'ù':'u', 'Ù':'U', 'û':'u', 'Û':'U',
                 'ñ':'n', 'Ñ':'N'}
    if isinstance(text, str):
        out = ''
        for char in text:
            if ord(char) > 127:
                if char in repl_dict:
                    out += repl_dict[char]
                else:
                    out += '?'
            else:
                out += char
        return out
    if text is None:
        return ''
    raise TypeError('str2ascii() expects a string!')


def error_to_html(exc):
    """Format a Python exception in HTML

    Arguments:
        exc_info: output of sys.exc_info()
    """
    out = ('<pre><code class="error">I\'m, sorry it looks like an error '
           'occured!\n\n\n{}</code></pre>'.format(str2html(exc)))
    return out


if __name__ == '__main__':
    pass
