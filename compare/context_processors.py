from .utils import get_compare_ids


def compare(request):
    ids = get_compare_ids(request)
    return {'compare_ids': ids, 'compare_count': len(ids)}
