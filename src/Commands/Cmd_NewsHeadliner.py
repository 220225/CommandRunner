import datetime
import json
import tempfile
import webbrowser
from dataclasses import dataclass, field

from contextlib import suppress

with suppress(ModuleNotFoundError):
    import requests

import Core
from CommandBase import CommandBase

logger = Core.get_logger()


@dataclass
class Cmd_NewsHeadliner(CommandBase):
    label = "News Headliner"
    tooltip = "Get the latest news headliners from the News API"

    # dataclass fields for command parameters
    country_code: str = field(
        default="us", metadata={"help": "Country Code", "items": ["us", "jp", "tw"]}
    )
    query: str = field(default="", metadata={"help": "Query string without space"})
    category: str = field(
        default="all",
        metadata={
            "help": "Category",
            "items": [
                "all",
                "business",
                "entertainment",
                "health",
                "science",
                "sports",
                "technology",
            ],
        },
    )
    api_key: str = field(default="", metadata={"help": "API Key"})

    def run(self, data={}):
        country_code = data["country_code"]
        category = data["category"]
        api_key = data["api_key"]
        query = data["query"]

        date_28_days_ago = datetime.datetime.now() - datetime.timedelta(days=28)
        date_28_days_ago_str = date_28_days_ago.strftime("%Y-%m-%d")
        request_url = f"https://newsapi.org/v2/top-headlines?country={country_code}"

        if category != "all":
            request_url += f"&category={category}"

        if query != "":
            request_url += f"&q={query}"
            request_url += f"&from={date_28_days_ago_str}-01-01&apiKey={api_key}"
        else:
            request_url += f"&apiKey={api_key}"

        logger.info(f"Request URL: {request_url}")
        try:
            news = requests.get(request_url)
        except requests.exceptions.RequestException as e:
            logger.error(f"RequestException: {e}", exc_info=True)

        data = json.loads(news.content)

        links = []
        for article in data.get("articles", []):
            links.append(
                {"Link": article["url"], "Title": article["title"], "Votes": 0}
            )

        if not links:
            html = Core.generate_html_content_with_text(
                data, title="Top Headlines News Result"
            )
        else:
            html = Core.generate_html_content_with_links(
                links,
                title=f"Top Headlines News: {country_code}, Category: {category}",
                with_votes=False,
            )

        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
            f.write(html.encode("utf-8"))
            webbrowser.open_new_tab(f.name)
