# general util helper methods

import sys
import traceback


def normalize_truthiness(value):
    true_values = ['y', 'yes', '1', 'true']
    false_values = ['n', 'no', '0', 'false']

    if str(value).lower() in true_values:
        return True
    elif str(value).lower() in false_values:
        return False
    else:
        raise ValueError(
            "Unsupported value (%s) for truthiness. Accepted values: "
            "truthy - %s, falsy - %s" % (value, true_values, false_values)
        )


def logException(log_fn, message=None):
    """ A helper to dump exceptions with log filtered prefix
    Useful for when you need to grep a log"""

    tb_type, tb_value, tb_traceback = sys.exc_info()
    if message is None:
        message = ""
    else:
        message = "%s\n" % message
    for s in traceback.format_exception(tb_type, tb_value, tb_traceback):
        message += "%s\n" % s
    for line in message.split("\n"):
        log_fn(line)
