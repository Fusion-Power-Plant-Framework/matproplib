import re
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options

import re
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options


class DOIPlugin(BasePlugin):
    config_scheme = (
        ("doi_prefix", config_options.Type(str, default="https://doi.org/")),
    )

    def on_page_content(self, html, **kwargs):
        pattern = re.compile(
        r"""\.\.\s*doi::\s*  # .. doi::
        (?P<doi>\b10\.[0-9]{4,}(?:\.[0-9]+)*/(?:(?!["&'<>])\S)+)\b  # doi regex
        (?:\s*:title:\s*(?P<title>.*?)(?=\n\S|$))?  # optional title
    """,

            re.IGNORECASE | re.VERBOSE | re.DOTALL
        )


        def replace(match):
            doi = match.group("doi")
            title = match.group("title")
            link_text = title.strip() if title else f"DOI: {doi}"
            href = f'{self.config["doi_prefix"]}{doi}'
            return f'<p><a href="{href}">{link_text}</a></p>'

        return pattern.sub(replace, html)
