def is_number(item):
    try:
        float(item)
        return True
    except:
        return False


def is_string(item):
    return isinstance(item, str)


def normalize_list_format(array):
    array = list(array)
    if not array:
        return []
    first = array[0]
    if is_number(array[0]):
        return [round(num, 2) for num in array]
    return array
