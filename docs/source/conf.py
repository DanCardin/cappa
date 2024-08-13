from sphinx_pyproject import SphinxConfig

config = SphinxConfig("../../pyproject.toml")

project = "Cappa"
copyright = "2023, Dan Cardin"
author = config.author
release = config.version

extensions = [
    "autoapi.extension",
    "myst_parser",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "sphinx_togglebutton",
]

templates_path = ["_templates"]

exclude_patterns = []

html_theme = "furo"
html_theme_options = {
    "navigation_with_keys": True,
}
html_static_path = ["_static"]

myst_heading_anchors = 4
myst_enable_extensions = [
    "amsmath",
    "colon_fence",
    "deflist",
    "dollarmath",
    "fieldlist",
    "html_admonition",
    "html_image",
    "linkify",
    "replacements",
    "smartquotes",
    "strikethrough",
    "substitution",
    "tasklist",
]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

autoapi_type = "python"
autoapi_dirs = ["../../src/cappa"]
autoapi_generate_api_docs = False

autodoc_typehints = "description"
autodoc_typehints_format = "fully-qualified"
suppress_warnings = ["autoapi.python_import_resolution"]

autosectionlabel_prefix_document = True
