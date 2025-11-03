from importlib.resources.abc import Traversable
from _pytest import config
import pytest
from pkg.src.scraper_config_handler import (
    _defaults_root,
    ScraperConfigHandler,
    ScraperConfigHandlerError,
    TargetConfig,
)
from textwrap import dedent
from pkg import FILES
import json


@pytest.fixture
def good_json_filler():
    return dedent("""\
       {
          "famous_painters":
            {
              "group_name": "artworks",
              "tiles_tag_class": "wDYxhc",
              "tiles_tag_attr": "kc:/visual_art/visual_artist:works",
              "item_tag_class": "iELo6",
              "name_tag_class": "pgNMRc",
              "year_tag_class": "cxzHyb",
              "image_tag_class": "taFZJe"
            },
          "famous_musicians":
            {
              "group_name": "artworks",
              "tiles_tag_class": "wDYxhc NFQFxe",
              "tiles_tag_attr": "NULL",
              "item_tag_class": "XRVJtc bnmjfe aKByQb",
              "name_tag_class": "NULL",
              "year_tag_class": "NULL",
              "image_tag_class": "NULL"
            }
        }
    """)


@pytest.fixture
def bad_json_filler():
    return dedent("""\
       {
          "famous_painters":
            {
              "group_name": "albums",
              "tiles_tag_class": "wDYxhc",
              "tiles_tag_attr": "kc:/visual_art/visual_artist:works",
              "item_tag_class": "iELo6",
              "name_tag_class": "pgNMRc",
              "year_tag_class": "cxzHyb",
              "image_tag_class": "taFZJe"
            }
          "famous_musicians":
            {
              "group_name": "albums",
              "tiles_tag_class": "wDYxhc NFQFxe",
              "tiles_tag_attr": "NULL",
              "item_tag_class": "XRVJtc bnmjfe aKByQb",
              "name_tag_class": "NULL",
              "year_tag_class": "NULL",
              "image_tag_class": "NULL"
            }
        }
    """)


def test_defaults_root():
    assert isinstance(_defaults_root(), Traversable)


def test_read(tmp_path, good_json_filler):
    config_fname = "cfg.json"
    cpath = tmp_path / config_fname

    with open(cpath, "w") as f:
        f.write(good_json_filler)

    cfg = ScraperConfigHandler.read(
        config_source_path=cpath,
    )

    assert [k in {"famous_painters", "famous_musicians"} for k in cfg._config.keys()]


def test_from_defaults():
    cfg = ScraperConfigHandler.from_defaults()
    assert cfg._config["famous_painters"]["item_tag_class"] == "iELo6"
    assert cfg._config["famous_musicians"]["year_tag_class"] == "NULL"


def test_select():
    cfg = ScraperConfigHandler.from_defaults()
    target = cfg.select("famous_painters")
    assert isinstance(target, TargetConfig)
    assert target.item_tag_class == "iELo6"


def test_options():
    cfg = ScraperConfigHandler.from_defaults()
    direct = json.loads(FILES.joinpath("config.json").read_text())
    assert set(cfg.options) == set(tuple(k for k in direct.keys()))


def test_set_defaults():
    other_file = "van-gogh-paintings-search-header.json"
    ScraperConfigHandler._set_default_filename(config_filename=other_file)
    cfg = ScraperConfigHandler.from_defaults()
    vangogh_keys = json.loads(FILES.joinpath(other_file).read_text(encoding="utf-8"))
    assert [k in vangogh_keys for k in cfg._config.keys()]


def test_set():
    cfg = ScraperConfigHandler.from_defaults()
    assert isinstance(cfg._config, dict)
    cfg._set(attr="_config", val=123)
    assert isinstance(cfg._config, int)
    assert cfg._config == 123


def test_bad_json_exception(tmp_path, bad_json_filler):
    bad_json_fname = "bad_data.json"
    nonexistent_fname = "I_dont_exist.txt"

    bad_json_file = tmp_path / bad_json_fname

    with open(bad_json_file, "w") as f:
        f.write(bad_json_filler)

    with pytest.raises(
        ScraperConfigHandlerError, match=f"Could not parse json payload*"
    ):
        _ = ScraperConfigHandler._reader(
            _root=tmp_path,
            _fname=bad_json_fname,
        )
    with pytest.raises(ScraperConfigHandlerError, match="Default file not found*"):
        _ = ScraperConfigHandler._reader(
            _root=tmp_path,
            _fname=nonexistent_fname,
        )
