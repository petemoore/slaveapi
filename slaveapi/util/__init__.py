# general util helper methods


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
