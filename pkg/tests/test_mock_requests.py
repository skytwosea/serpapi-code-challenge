from importlib.resources.abc import Traversable
import pytest
from pkg.src.mock_requests import (
    _defaults_root,
    MockRequests,
    MockRequestsError,
    MockResponse,
)
from pkg import FILES
import json
from textwrap import dedent

@pytest.fixture
def good_json_filler():
    return dedent("""\
       {
          "famous_painters":
            {
              "check_tag": {"class": "wDYxhc", "data-attrid": "kc:/visual_art/visual_artist:works", "data-md": "467"},
              "item_tag": "iElo6",
              "name_tag_class": "pgNMRc",
              "ext_tag_class": "taFZJe",
              "image_tag_class": "NULL"
            },
          "famous_musicians":
            {
              "check_tag": {"class": "wDYxhc NFQFxe", "data-attrid": "kc:/music/artist:albums", "data-md": "228"},
              "item_tag": "XRVJtc bnmjfe aKByQb",
              "name_tag_class": "NULL",
              "ext_tag_class": "NULL",
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
              "check_tag": {"class": "wDYxhc", "data-attrid": "kc:/visual_art/visual_artist:works", "data-md": "467"},
              "item_tag": "iElo6",
              "name_tag_class": "pgNMRc",
              "ext_tag_class": "taFZJe",
              "image_tag_class": "NULL"
            }
          "famous_musicians":
            {
              "check_tag": {"class": "wDYxhc NFQFxe", "data-attrid": "kc:/music/artist:albums", "data-md": "228"},
              "item_tag": "XRVJtc bnmjfe aKByQb",
              "name_tag_class": "NULL",
              "ext_tag_class": "NULL",
              "image_tag_class": "NULL"
            }
        }
    """)

def test_defaults_root():
    assert isinstance(_defaults_root(), Traversable)

def test_read(tmp_path, good_json_filler):
    content_text = "In a hole in the ground there lived a Hobbit."

    header_fname = "header.json"
    content_fname = "content.txt"

    hpath = tmp_path / header_fname
    cpath = tmp_path / content_fname

    with open(hpath, "w") as f:
        f.write(dedent(good_json_filler))
    with open(cpath, "w") as f:
        f.write(content_text)

    mr = MockRequests.read(
        header_source_path=hpath,
        content_source_path=cpath,
    )

    assert [k in {"famous_painters", "famous_musicians"} for k in mr._header.keys()]
    assert mr._content.decode(encoding="utf-8") == "In a hole in the ground there lived a Hobbit."
    assert mr._status_code == 200


def test_from_defaults():
    mr = MockRequests.from_defaults()
    assert mr._status_code == 200
    assert mr._header["Server"] == "gws"
    assert isinstance(mr._content, bytes)

def test_get():
    mr = MockRequests.from_defaults()
    response = mr.get()
    assert isinstance(response, MockResponse)
    assert response.status_code == 200
    assert response.header["Server"] == "gws"
    assert isinstance(response.content, bytes)

def test_set_defaults():
    other_file = "config.json"
    MockRequests._set_default_filenames(header_filename=other_file)
    mr = MockRequests.from_defaults()
    config_keys = json.loads(
        FILES.joinpath(other_file).read_text(encoding="utf-8")
    )
    assert [k in config_keys for k in mr._header.keys()]

def test_set():
    mr = MockRequests.from_defaults()
    assert isinstance(mr._content, bytes)
    mr._set(
        attr="_content",
        val="In a hole in the ground there lived a Hobbit.")
    assert isinstance(mr._content, str)
    assert mr._content == "In a hole in the ground there lived a Hobbit."

def test_bad_json_exeption(tmp_path, good_json_filler, bad_json_filler):
    t_content = "In a hole in the ground there lived a Hobbit."

    good_json_fname = "good_data.json"
    broken_json_fname = "broken_data.json"
    bad_content_fname = "bad_content.txt"
    nonexistent_fname = "I_dont_exist.txt"

    good_json_file = tmp_path / good_json_fname
    broken_json_file = tmp_path / broken_json_fname
    bad_content_file = tmp_path / bad_content_fname

    with open(good_json_file, "w") as f:
        f.write(good_json_filler)
    with open(broken_json_file, "w") as f:
        f.write(bad_json_filler)
    with open(bad_content_file, "w") as f:
        f.write(t_content)

    with pytest.raises(
        MockRequestsError,
        match=f"Could not parse json payload*"
    ):
        _ = MockRequests._reader(
            _header_root=tmp_path,
            _content_root=tmp_path,
            _header_name=broken_json_fname,
            _content_name=bad_content_file,
        )
    with pytest.raises(
        MockRequestsError,
        match=f"Default file not found*"
    ):
        _ = MockRequests._reader(
            _header_root=tmp_path,
            _content_root=tmp_path,
            _header_name=good_json_fname,
            _content_name=nonexistent_fname,
        )