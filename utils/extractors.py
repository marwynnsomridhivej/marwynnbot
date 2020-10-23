from operator import attrgetter
from typing import Any, Iterable, List, Union


def extract(iterable: Iterable, iter_in: List) -> Union[str, None]:
    for item in iterable:
        if item in iter_in:
            return item
    else:
        return None


def extract_attr(iterable: Iterable, attrs: str = None) -> Union[Any, None]:
    try:
        attrs, eq = attrs.replace(" ", "").split("=")
    except Exception:
        raise ValueError("attrs must be specified in the format attr1.attr2...attrn=value")

    get = attrgetter(attrs)

    for item in iterable:
        try:
            result = get(item)
            if result == eq:
                return item
        except Exception:
            pass
    return None


def extract_all_attr(iterable: Iterable, attrs: str = None) -> Union[List[Any], None]:
    try:
        attrs, eq = attrs.replace(" ", "").split("=")
    except Exception:
        raise ValueError("attrs must be specified in the format attr1.attr2...attrn=value")

    results = []
    get = attrgetter(attrs)

    for item in iterable:
        try:
            result = get(item)
            if result == eq:
                results.append(item)
        except Exception:
            pass

    return results or None
