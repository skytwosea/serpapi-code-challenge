import re
from pkg.src.static_strategy import (
    _RE_FN_PATTERN,
)


def test_function_call_regex():
    valid_permutations = [
        "_setImagesSrc(ii,r,s)",
        "_setImagesSrc(ii,s,r)",
        "_setImagesSrc(r,ii,s)",
        "_setImagesSrc(r,s,ii)",
        "_setImagesSrc(s,ii,r)",
        "_setImagesSrc(s,r,ii)",
        "_setImagesSrc( ii,r,s)",
        "_setImagesSrc(ii ,s,r)",
        "_setImagesSrc(r,ii ,s)",
        "_setImagesSrc(r,s, ii)",
        "_setImagesSrc(s, ii,r)",
        "_setImagesSrc(s,r,ii)",
        "_setImagesSrc(ii,r ,s)",
        "_setImagesSrc(ii,s,r)",
        "_setImagesSrc(r, ii,s)",
        "_setImagesSrc( r,s,ii)",
        "_setImagesSrc(s,ii, r)",
        "_setImagesSrc(s,r,ii )",
    ]
    invalid_permutations = [
        "_setImagesSrc(ii,ii,s)",
        "_setImagesSrc(ii,s,s)",
        "_setImagesSrc(r,ii,r)",
        "_setImagesSrc(s,s,s)",
        "_setImagesSrc(r,r,r)",
        "_setImagesSrc(ii,ii,ii)",
        "_SetImagesSrc( ii,r,s)",
        "_setimagesSrc(ii,r ,s)",
    ]
    for item in valid_permutations:
        assert bool(_RE_FN_PATTERN.search(item))
    for item in invalid_permutations:
        assert not bool(_RE_FN_PATTERN.search(item))
