"""
Created on 2024-03-29

@author: wf
"""
from dataclasses import dataclass

import geograpy


@dataclass
class Version:
    """
    Version handling for the geograpy3 project.
    """

    name = "geograpy3"
    version = geograpy.__version__
    date = "2023-09-10"
    updated = "2024-03-29"
    description = "Extract countries, regions, and cities from a URL or text"

    authors = "Somnath Rakshit, Wolfgang Fahl, Tim Holzheim"  # Combining all authors into a single string

    doc_url = "https://geograpy3.readthedocs.io"
    chat_url = "https://github.com/somnathrakshit/geograpy3/discussions"
    cm_url = "https://github.com/somnathrakshit/geograpy3"

    license = """Copyright 2023-2024 contributors. All rights reserved.

    Licensed under the Apache License 2.0
    http://www.apache.org/licenses/LICENSE-2.0

    Distributed on an "AS IS" basis without warranties
    or conditions of any kind, either express or implied."""

    longDescription = f"""{name} version {version}
{description}

    Created by {authors} on {date} last updated {updated}.
    For more information, visit {doc_url}."""
