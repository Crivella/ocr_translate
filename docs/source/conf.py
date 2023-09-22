# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ocr_translate'
copyright = '2023, Davide Grassano'
author = 'Davide Grassano'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.extlinks',
    'sphinx_design',
    'sphinx_rtd_dark_mode',
    'sphinxcontrib.openapi',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for extlinks extension -------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html#module-sphinx.ext.extlinks
extlinks = {
    'github': ('https://github.com/Crivella/ocr_translate/%s', ''),
    'dockerhub': ('https://hub.docker.com/r/crivella1/ocr_translate/%s', ''),
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

default_dark_mode = True
html_theme = 'rtd'
html_static_path = ['_static']
