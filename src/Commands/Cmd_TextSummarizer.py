import tempfile
import webbrowser
from CommandBase import CommandBase
import Core

logger = Core.get_logger()


def generate_html_content_with_text(left_text, right_text):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Text Summarizer</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
            }}
            .container {{
                display: flex;
                flex-direction: row;
                justify-content: space-between;
            }}
            .left {{
                width: 48%;
            }}
            .right {{
                width: 48%;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="left">
                {left_text}
            </div>
            <div class="right">
                {right_text}
            </div>
        </div>
    </body>
    </html>
    """
    return html_content


class Cmd_TextSummarizer(CommandBase):
    label = "Text Summarizer"
    tooltip = "Summarize a text"
    ui_class = "CmdUI_TextSummarizer"

    def run(self, data={}):
        # speed up the lauching time when import this command
        from transformers import pipeline

        text_paragraph = data["text_paragraph"]

        summarizer = pipeline("summarization", model="philschmid/bart-large-cnn-samsum")
        summary = summarizer(
            text_paragraph, max_length=50, min_length=25, do_sample=False
        )

        html = generate_html_content_with_text(
            text_paragraph, summary[0]["summary_text"]
        )
        with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
            f.write(html.encode("utf-8"))
            webbrowser.open_new_tab(f.name)
