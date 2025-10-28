from pkg.src.scraper_config_handler import ScraperConfigHandler
from pkg.src.mock_requests import MockRequests
from pkg.src.serp_scraper import SerpScraper
from pkg.src.static_strategy import StaticStrategy
from bs4 import BeautifulSoup

rq = MockRequests.from_defaults()
response = rq.get()

# cfg = ScraperConfigHandler.from_defaults()
# tgt = cfg.select("famous_painters")

# scraper = SerpScraper(config=tgt)
strategy = StaticStrategy()
soup = BeautifulSoup(response.content, "html.parser")

scripts = [
    script.get_text() for script in
    soup.find_all("script")
]
scripts = list(filter(strategy._quickcheck, scripts))
img_url_map = {}
for script in scripts:
    ast = strategy._parse_js(script)
    var_declarations = strategy._get_var_decls(ast)
    mapping = strategy._extract_values_from_declarations(var_declarations)
    img_url_map.update(mapping)

print(vars().keys())


# result = scraper._extract_via_attrs(soup)
# payloads_map = scraper._build_injected_urls_map(soup)
# scraper._inject_valid_urls(result, payloads_map)
