import pytest

from pkg.src.static_strategy import (
    _RE_FN_PATTERN,
    StaticStrategy,
    HydrationScriptASTVisitor,
)

from pkg.src.serp_scraper import (
    SerpItem,
    SerpResult,
)

@pytest.fixture
def serp_result_components():
    si_0 = SerpItem(
        rank=0,
        name="Bilbo",
        extensions=["Frodo", "Sam"],
        link="Bag End",
        img_id="Hobbiton",
        image="unknown_0",
    )
    si_1 = SerpItem(
        rank=1,
        name="Gandalf",
        extensions=["Gimli", "Legolas"],
        link="Rivendell",
        img_id="Middle Earth",
        image="unknown_0",
    )
    result = SerpResult(
        name="Lord of the Rings",
        items=[si_0, si_1,],
    )
    return [si_0, si_1, result]

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
    "setImagesSrc(ii, r, s)",
    "_setimagessrc(r,ii,s)",
]

def test_function_call_regex():
    for item in valid_permutations:
        assert bool(_RE_FN_PATTERN.search(item))
    for item in invalid_permutations:
        assert not bool(_RE_FN_PATTERN.search(item))

def test_StaticStrategy_re_check(serp_result_components):
    _, _, result = serp_result_components
    strat = StaticStrategy()
    for item in valid_permutations:
        assert strat._re_check(item)
    for item in invalid_permutations:
        assert not strat._re_check(item)

def test_StaticStrategy_inject_valid_urls(serp_result_components):
    edits_map = {
        "Hobbiton": "The Shire",
        "Middle Earth": "Mirkwood",
    }

    strat = StaticStrategy()
    strat.edits_map = edits_map

    si_0, si_1, result = serp_result_components

    assert result.items[0].image is si_0.image

    strat._inject_valid_urls(result)

    assert result.items[0].image == "The Shire"
    assert result.items[1].image == "Mirkwood"

    assert result.items[1].image is si_1.image
