
def split_list(list_object, segment_size):
    result_list = []
    for i in range(len(list_object) // segment_size + 1):
        begin = i * segment_size
        end = (i + 1) * segment_size
        if begin < len(list_object):
            result_list.append(list_object[begin:end])
    return result_list
