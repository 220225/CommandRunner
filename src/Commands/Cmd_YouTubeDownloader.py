from contextlib import suppress
from dataclasses import dataclass, field

with suppress(ModuleNotFoundError):
    import yt_dlp

import Core
from CommandBase import CommandBase

logger = Core.get_logger()


@dataclass
class Cmd_YouTubeDownloader(CommandBase):
    label = "YouTube Downloader"
    tooltip = "Download a YouTube video"

    # dataclass fields for command parameters
    url: str = field(default="", metadata={"help": "YouTube URL"})

    def run(self, data={}):
        url = data["url"]

        try:
            ydl_opts = {
                "format": "bestvideo+bestaudio",
                "merge_output_format": "mp4",
                "outtmpl": "%(title)s.%(ext)s",
            }
            # Download the video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

        except Exception as e:
            logger.error(f"Exception: {e}", exc_info=True)
