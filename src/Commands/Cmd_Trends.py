import tempfile
import webbrowser
from contextlib import suppress
from dataclasses import dataclass, field

with suppress(ModuleNotFoundError):
    from trendspy import Trends

import Core
from CommandBase import CommandBase

logger = Core.get_logger("Cmd_Trends")


@dataclass
class Cmd_Trends(CommandBase):
    label = "Trends"
    tooltip = "Get trending news"

    # dataclass fields for command parameters
    country_code: str = field(
        default="TW",
        metadata={"help": "Country Code", "items": ["US", "TW"]},
    )
    start_idx: int = field(default=0, metadata={"help": "Start index of trends"})
    count: int = field(default=10, metadata={"help": "Number of trends to display"})

    def run(self, data={}):
        country_code = data["country_code"]
        count = data["count"]
        start_idx = data["start_idx"]

        try:
            tr = Trends()

            trends = tr.trending_now(geo=country_code)
            logger.info(f"Got {len(trends)} trend items\n\nFirst trend item:")

            cur_idx = 0
            for trend in trends:
                if cur_idx < start_idx:
                    cur_idx += 1
                    continue

                if cur_idx >= start_idx + count:
                    break

                if not trend.news_tokens:
                    continue

                logger.info(f"Index: {cur_idx}")
                news = []
                try:
                    news = tr.trending_now_news_by_ids(
                        trend.news_tokens,
                        max_news=20,
                    )
                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)

                hn = []
                for article in news:
                    hn.append(
                        {
                            "Title": article.title,
                            "Link": article.url,
                            "Votes": article.source,
                        }
                    )
                else:
                    html = Core.generate_html_content_with_links(
                        hn, title=f"Trends News [{cur_idx}]: {trend.keyword} "
                    )

                    # generate temp html file and open it in browser
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
                        f.write(html.encode("utf-8"))
                        webbrowser.open_new_tab(f.name)

                cur_idx += 1

        except Exception as e:
            logger.error(f"Exception: {e}", exc_info=True)
