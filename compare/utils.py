SESSION_KEY = 'compare_product_ids'
MAX_COMPARE_ITEMS = 4


def get_compare_ids(request):
    return request.session.get(SESSION_KEY, [])


def add_to_compare(request, product_id):
    ids = get_compare_ids(request)
    product_id = int(product_id)
    if product_id not in ids:
        ids.append(product_id)
        ids = ids[-MAX_COMPARE_ITEMS:]  # keep only the most recent N
    request.session[SESSION_KEY] = ids
    return ids


def remove_from_compare(request, product_id):
    ids = get_compare_ids(request)
    product_id = int(product_id)
    if product_id in ids:
        ids.remove(product_id)
    request.session[SESSION_KEY] = ids
    return ids


def clear_compare(request):
    request.session[SESSION_KEY] = []
