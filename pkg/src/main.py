from pkg.src.scraper_config_handler import ScraperConfigHandler
from pkg.src.mock_requests import MockRequests
from pkg.src.serp_scraper import SerpScraper
from pkg.src.static_strategy import StaticStrategy
from pkg import FILES

rq = MockRequests.from_defaults()
response = rq.get()

config = ScraperConfigHandler.from_defaults().select("famous_painters")
strategy = StaticStrategy()

scraper = SerpScraper(config=config, strategy=strategy)
result = scraper.scrape(response.content).to_json()

with open(str(FILES.joinpath("output.json")), "w", encoding="utf-8") as f:
    f.write(result)
