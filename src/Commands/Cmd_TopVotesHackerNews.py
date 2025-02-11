import tempfile
import webbrowser
from dataclasses import dataclass, field

import requests
from bs4 import BeautifulSoup as bs

import Core
from CommandBase import CommandBase

logger = Core.get_logger()


def generate_html_content_with_links_for_hackernews(links, title=""):
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
    """
    html_content += f"<title>{title}</title>"

    html_content += """
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 20px;
            }
            h1 {
                font-size: 48px;
                color: #333;
            }
            ul {
                list-style-type: none;
                padding: 0;
            }
            li {
                background-color: #fff;
                margin: 10px 0;
                padding: 15px;
                border-radius: 5px;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            }
            a {
                text-decoration: none;
                color: #007bff;
                font-weight: bold;
            }
            a:hover {
                text-decoration: underline;
            }
            .votes {
                color: #555;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
    """
    html_content += f"<h1>{title}</h1>"
    html_content += """
    <ul>
    """

    for link in links:
        try:
            html_content += f'<li><a href="{link["Link"]}">{link["Title"]}</a> - Votes: {link["Votes"]} - <a href="{link["Comments"]}">Comments</a></li>'
        except Exception as e:
            logger.error(f"Exception: {e}")

    html_content += """
        </ul>
    </body>
    </html>
    """

    return html_content


# NOTE: https://github.com/slegro97/custom-hacker-news/blob/main/scrape.py


def sort_by_votes(hnlist):
    return sorted(hnlist, key=lambda k: k["Votes"], reverse=True)


def create_custom_hn(url, links_arg, subtext_arg):
    hn = []
    for i, item in enumerate(links_arg):
        title = item.getText()
        href = item.get("href", None)
        vote = subtext_arg[i].select(".score")

        comments_link = url
        try:
            comments_link = url + subtext_arg[i].select("a")[1].get("href", None)
        except Exception as e:
            logger.error(f"Exception: {e}", exc_info=True)

        if len(vote):
            points = int(vote[0].getText().replace(" points", ""))
            if points > 99:
                hn.append(
                    {
                        "Title": title,
                        "Link": href,
                        "Votes": points,
                        "Comments": comments_link,
                    }
                )

    return sort_by_votes(hn)


@dataclass
class Cmd_TopVotesHackerNews(CommandBase):
    label = "Top Votes Hacker News"
    tooltip = "Get the top votes hacker news"

    # dataclass fields for command parameters
    url: str = field(
        default="https://news.ycombinator.com/", metadata={"help": "website url"}
    )
    num_top_votes: int = field(
        default=20, metadata={"help": "Number of top votes to display"}
    )
    num_pages: int = field(
        default=5, metadata={"help": "Number of pages to scrape"}
    )

    def run(self, data={}):
        url = data["url"]
        num_top_votes = data["num_top_votes"]
        num_pages = data["num_pages"]

        all_links = []
        for page in range(1, num_pages + 1):
            req = requests.get(f"{url}?p={page}")

            soup = bs(req.text, "html.parser")

            links = soup.select(".titleline > a")
            subtext = soup.select(".subtext")

            all_links.extend(create_custom_hn(url, links, subtext))

        all_links = sort_by_votes(all_links)
        all_links = all_links[:num_top_votes]
        html = generate_html_content_with_links_for_hackernews(
            all_links,
            title="Top Votes Hacker News",
        )

        # generate temp html file and open it in browser
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
            f.write(html.encode("utf-8"))
            webbrowser.open_new_tab(f.name)
