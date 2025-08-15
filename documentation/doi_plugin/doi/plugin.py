# SPDX-FileCopyrightText: 2025-present The Bluemira Developers <https://github.com/Fusion-Power-Plant-Framework/bluemira>
#
# SPDX-License-Identifier: MIT
"""mkdocs plugin for formatting dois as links"""

import re

from mkdocs.config import config_options
from mkdocs.plugins import BasePlugin


class DOIPlugin(BasePlugin):
    """Modify doi links"""

    config_scheme = (
        ("doi_prefix", config_options.Type(str, default="https://doi.org/")),
    )

    def on_page_content(self, html: str, **kwargs) -> str:  # noqa: ARG002
        """Modify doi links in html

        Returns
        -------
        :
            Modified html
        """
        pattern = re.compile(
            r"""\.\.\s*doi::\s*  # .. doi::
            (?P<doi>\b10\.[0-9]{4,}(?:\.[0-9]+)*/(?:(?!["&'<>])\S)+)\b  # doi regex
            (?:\s*:title:\s*(?P<title>.*?)(?=\n\S|$))?  # optional title
            """,
            re.IGNORECASE | re.VERBOSE | re.DOTALL,
        )

        def replace(match: re.Match) -> str:
            """Replace .. doi:: with link"""  # noqa: DOC201
            doi = match.group("doi")
            title = match.group("title")
            link_text = title.strip() if title else f"DOI: {doi}"
            href = f"{self.config['doi_prefix']}{doi}"
            return f'<p><a href="{href}">{link_text}</a></p>'

        return pattern.sub(replace, html)
