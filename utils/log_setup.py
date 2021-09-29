#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""Module for setting up logging.

Last edit: 2018-12-9

Usage:
    To initialize colored log for the shell and also writing to a file:

        setup('log/MYLOG_%Y-%m-%dT%H%M%S.log')

    To setup log in shell without writing to file:

        setup(lvl_file=None)

    To change both levels individually:

        setup('log/MYLOG_%Y-%m-%dT%H%M%S.log', lvl_bash=logging.DEBUG,
              lvl_file=logging.ERROR)
"""
import logging
import os
import time


def setup(logfile='log/%Y/%m/d/log_%Y-%m%dT%H%M%S.log', *, color=True,
          debug_file=True, lvl_bash=logging.INFO, lvl_file=logging.WARNING,
          symlink='log'):
    """Initialize logging.

    Optional Arguments:
        logfile (str): Directory and filename of log. Interpreted by
                       `time.strftime`.
                       (Default 'log/%Y/%m/d/log_%Y-%m%dT%H%M%S.log')
    Keyword-only Arguments:
        color (bool): Whether to use colorcodes for bash output. (Default True)
        debug_file (bool): Whether to create a hidden file with all debug
                           messages next to the logfile (Default True)
        lvl_bash (int/None): Level of the bash output. Set to `None` for
                             no output. (Default `logging.INFO`)
        lvl_file (int/None): Level of the log file. Set to `None` for
                             no logfile. (Default `logging.WARNING`)
        symlink (str/None): Directory for a symbolic link pointing to the
                            most recent log. Set to None for no link.
                            (Default 'log')
    """
    root = logging.getLogger()
    map(root.removeHandler, root.handlers[:])
    map(root.removeFilter, root.filters[:])
    root.handlers = []
    root.filters = []
    root.setLevel(0)

    # Shell output
    if lvl_bash is not None:
        _ch = logging.StreamHandler()
        _ch.setLevel(lvl_bash)
        if color:
            _ch.setFormatter(ColoredFormatter())
        else:
            _ch.setFormatter(LevelFormatter())
        root.addHandler(_ch)

    # File output
    if lvl_file is not None:
        logfile = time.strftime(logfile)

        # Create log directory
        _logdir = os.path.dirname(logfile)
        if _logdir and not os.path.exists(_logdir):
            logging.warning('Creating new directory %s', _logdir)
            os.makedirs(_logdir)
        elif _logdir and not os.path.isdir(_logdir):
            logging.error('Log directory "%s" exists but is '
                          'not a directory!', _logdir)

        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(lvl_file)
        file_handler.setFormatter(LevelFormatter())
        root.addHandler(file_handler)

        # Update symlink to newest log
        if symlink is not None:
            _path = os.path.join(symlink, 'recent.log')
            try:
                os.remove(_path)
            except FileNotFoundError:
                pass
            try:
                os.symlink(os.path.abspath(logfile), _path)
            except OSError:
                logging.warning('Cannot create symlinks.')

        # Add a hidden log file with level DEBUG
        if debug_file:
            _path, _file = os.path.split(logfile)
            _name, _ext = os.path.splitext(_file)
            debug_logfile = os.path.join(_path, '.' + _name + '_DEBUG' + _ext)
            file_handler = logging.FileHandler(debug_logfile)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(LevelFormatter())
            root.addHandler(file_handler)

            # Update symlink to newest log
            if symlink is not None:
                _path = os.path.join(symlink, '.recent_DEBUG.log')
                try:
                    os.remove(_path)
                except FileNotFoundError:
                    pass
                try:
                    os.symlink(os.path.abspath(debug_logfile), _path)
                except OSError:
                    logging.warning('Cannot create symlinks.')

#        if lvl_bash is not None:
#            logging.info('Log enabled. Log file is located at %s', logfile)

    return root


class LevelFormatter(logging.Formatter):
    """Custom Formatter with different style per log level."""
    def __init__(self, fmt=None, datefmt='%Y-%m-%d %H:%M:%S',
                 default_fmt='{asctime} {levelname}: {message}'):
        """Allowing custom log format per log-level.

        Optional Arguments:
            fmt (dict): The dictionary should be of the form
                {logging.DEBUG: '...', ...}, i.e. the keys should be
                level numbers comming from `record.levelno`. (Default None)
            datefmt (str):
            default_fmt (str):
        """
        self.level_fmt = {
            logging.DEBUG: '{asctime} {levelname}'
                           '[{filename}:l.{lineno}]: {message}',
            logging.INFO: '{asctime} {name}[{process:d}] '
                          '{levelname}: {message}'}
        if fmt is not None:
            self.level_fmt.update(fmt)

        super().__init__(fmt=default_fmt, datefmt=datefmt, style='{')

    def format(self, record):
        """Replace format string temporarly depending on loglevel.

        Arguments:
            record: See `logging.Formatter.format` for help.
        """
        # Store default format
        # pylint: disable=protected-access
        original_fmt = self._style._fmt

        # Replace format temporarily
        if record.levelno in self.level_fmt:
            self._style._fmt = self.level_fmt[record.levelno]

        result = super().format(record)

        # Restore default format
        self._style._fmt = original_fmt

        return result


class ColoredFormatter(LevelFormatter):
    """Custom Formatter with colored output."""
    def __init__(self, fmt=None, **kwargs):
        """Colored logs.

        Optional Argmuents:
            fmt (dict): The dictionary should be of the form
                {logging.DEBUG: '...', ...}, i.e. the keys should be
                level numbers comming from `record.levelno`.
                Colors can be inserted with e.g. '$RED' or directly with
                the '\033[{}m' syntax. (Default None)

        List of predefined colors:
            $RESET, $BOLD,
            $BLACK, $RED, $GREEN, $YELLOW, $PINK, $VIOLET,
            $BROWN, $BLUE, $LIGHTBLUE, $ORANGE
        """
        if fmt is None:
            fmt = {logging.DEBUG:    '$GREEN{asctime} $BLACK$BOLD{levelname}'
                                     '$RESET[$BROWN{filename}:{lineno}$RESET]: '
                                     '$GREEN{message}',
                   logging.INFO:     '$GREEN{asctime} $BLACK$BOLD{levelname}'
                                     '$RESET: {message}',
                   logging.WARNING:  '$GREEN{asctime} $BLACK$BOLD{levelname}'
                                     '$RESET: $YELLOW{message}',
                   logging.ERROR:    '$GREEN{asctime} $BLACK$BOLD{levelname}'
                                     '$RESET: $BOLD$RED{message}',
                   logging.CRITICAL: '$GREEN{asctime} $BLACK$BOLD{levelname}'
                                     '$RESET: $BOLD$VIOLET{message}'}
        for key, val in fmt.items():
            fmt[key] = self._colorify(val)
        super().__init__(fmt=fmt, **kwargs)

    @staticmethod
    def _colorify(fmt):
        colors = {'$RESET':     0,
                  '$BOLD':      1,
                  '$BLACK':     30,
                  '$RED':       '38;5;1',
                  '$GREEN':     '38;5;2',
                  '$YELLOW':    '38;5;3',
                  '$PINK':      '38;5;13',
                  '$VIOLET':    '38;5;128',
                  '$BROWN':     '38;5;95',
                  '$BLUE':      '38;5;26',
                  '$LIGHTBLUE': '38;5;75',
                  '$ORANGE':    '38;5;208'}

        for key, val in colors.items():
            fmt = fmt.replace(key, '\033[{}m'.format(val))
        return fmt+'\033[0m'


if __name__ == '__main__':
    setup(lvl_file=None)

    logging.debug('A debug message')
    logging.info('An info message')
    logging.warning('A warning')
    logging.error('An error')
    logging.critical('Critical failure')
