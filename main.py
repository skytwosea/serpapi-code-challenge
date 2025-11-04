import sys
import difflib

from pkg import FILES
from pkg.src.scraper_config_handler import ScraperConfigHandler
from pkg.src.mock_requests import MockRequests
from pkg.src.serp_scraper import SerpScraper
from pkg.src.static_strategy import StaticStrategy
from pkg.src.dynamic_strategy import DynamicStrategy
from pkg.src.errors import ArgumentError


def _parse_args():
    if len(sys.argv) > 2:
        raise ArgumentError(
            "Main could not parse arguments.\n"
            "Available command line flags:\n"
            "-s or none:  use static strategy (default)\n"
            "-d        :  use dynamic strategy"
        )
    if len(sys.argv) == 1:
        return StaticStrategy()

    arg = sys.argv[1].strip()
    match arg:
        case "-s":
            return StaticStrategy()
        case "-d":
            return DynamicStrategy()
        case _:
            raise ArgumentError


def _diff_result() -> str:
    with open(str(FILES / "output.json")) as f:
        output = f.read()
    with open(str(FILES / "expected-array.json")) as f:
        expected = f.read()
    diff = list(
        difflib.unified_diff(output.splitlines(), expected.splitlines(), lineterm="")
    )
    if diff:
        return "\n".join(diff)
    else:
        return "ok"


def main():
    # get source html:
    rq = MockRequests.from_defaults()
    response = rq.get()

    # setup:
    config = ScraperConfigHandler.from_defaults().select("famous_painters")
    strategy = _parse_args()

    # run scraper:
    scraper = SerpScraper(config=config, strategy=strategy)
    result = scraper.scrape(response.content).to_json()

    # write:
    with open(str(FILES.joinpath("output.json")), "w", encoding="utf-8") as f:
        f.write(result)

    # check:
    print(_diff_result())


if __name__ == "__main__":
    main()
