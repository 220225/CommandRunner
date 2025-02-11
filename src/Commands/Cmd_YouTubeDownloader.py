from dataclasses import dataclass, field

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

        ydl_opts = {
            "format": "bestvideo+bestaudio",  # Download the best video and audio quality available
            "merge_output_format": "mp4",  # Merge video and audio into an MP4 file
            "outtmpl": "%(title)s.%(ext)s",  # Set the output filename template
        }
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
