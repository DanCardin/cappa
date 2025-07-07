import sys

sys.path.insert(0, ".")

project = "docutils"
copyright = "2025, docutils"
author = "docutils"
release = "docutils"

extensions = [
    "cappa.ext.docutils",
]

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store", ".venv"]
html_theme = "alabaster"
