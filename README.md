<div align="center">
  <p align="center">
	<a href="https://pypi.org/project/django-ocr_translate/"><img src="https://img.shields.io/pypi/dm/django-ocr_translate?style=flat-square" alt="pypi"/></a>
	<a href="https://pypi.org/project/django-ocr_translate/"><img src="https://img.shields.io/pypi/v/django-ocr_translate?style=flat-square" /></a>
	<a href="https://pypi.org/project/django-ocr_translate/"><img src="https://img.shields.io/github/downloads/Crivella/ocr_translate/total.svg?style=flat-square" /></a>
  <br />
	<a href="https://crivella.github.io/ocr_translate/"><img src="https://img.shields.io/badge/GitHub%20Pages-222222?style=for-the-badge&logo=GitHub%20Pages&logoColor=white" alt="pypi"/></a>
  </p>
</div>

# OCR_translate

This is a Django app for creating back-end server aimed at performing OCR and translation of images received via a POST request.

The OCR and translation is performed using freely available machine learning models and packages (see below for what is currently implemented).

The server is designed to be used together with [this browser extension](https://github.com/Crivella/ocr_extension), acting as a front-end providing the images and controlling the languages, models and plugins being used.

For more information, please consult the **[Full Documentation](https://crivella.github.io/ocr_translate/)**

## Running the server

See the [documentation](https://crivella.github.io/ocr_translate/user/index.html#running-the-server) for more information.

**TLDR:** If you are on windows you will need to:

- install [python](https://www.python.org/downloads/windows/) (3.10 or 3.11 as 3.12 is currently incompatible due to the version of numpy used [see #35](/../../issues/35)) with the check on `Add python.exe to PATH`
- download>unzip the [release file](/../../releases/latest/download/run_server.zip)
- run the `run-user.bat` file

### Why do I need to install python

Before version `v0.6.0` the server was distributed by including all possible plugins and their dependencies.\
This made the distribution file (both the github release and docker image) quite large and the release process cumbersome.\
Furthermore, not every user might be interested in every plugin and might end up downloading GB of files that they will never use.

For this reason a [plugin_manager](ocr_translate/plugin_manager.py) has been added to the project that will download/install the plugins and their dependencies on demand.\
Installing python packages requires `pip` to be available (which is included with python on the windows installer).\
Unfortunately I have not found a way to include pip reliably in the frozen install produced for the release file.\
The alternative would've been to add a 2nd installer just to get `pip` before running the server, but why reinvent the wheel.

The check on `Add python.exe to PATH` is needed so that `pip` can be run without having to make any assumption on the installation path.

Also since I am now asking people to install python, I decided to go all the way and use an approach similar to what [automatic1111's webui.bat](https://github.com/AUTOMATIC1111/stable-diffusion-webui/blob/master/webui.bat) does for stable diffusion.\
This batch script will create/reuse a virtual environment in a folder `venv` in the same directory as the script and install the required packages in it.

## Contributing

- Suggestions/Ideas are always welcome and can be posted as [discussions](https://github.com/Crivella/ocr_translate/discussions).\
  You can also just propose a new model to be tested/added to the ones available by default.
- Bugs can be reported as [issues](https://github.com/Crivella/ocr_translate/issues)
- Code contributions as [pull requests](https://github.com/Crivella/ocr_translate/pulls).
  Check [the documentation](https://crivella.github.io/ocr_translate/contrib/index.html) for more information.

## Plugins

The server is designed to only offer the basic functionalities, while the models that can be used and how they are used are defined by plugins.

See the documentation for a [list of available plugins](https://crivella.github.io/ocr_translate/plugins/index.html)

### Notes

- When switching the server between CPU/CUDA mode for the first time, run the installation of the plugins again to make sure the scope-specific dependencies are installed.
- Different plugins will make different types of models available:
  - `BOX Model`: EasyOcr, PaddleOCR
  - `OCR Model`: PaddleOCR, Tesseract, HuggingFace
  - `Translation Model`: HuggingFace, GoogleTranslate, Ollama

- Also some plugins might requires additional tools to be installed on the server and possibly some environment variable configured.
  Refer to the [plugin documentation](https://crivella.github.io/ocr_translate/plugins/index.html) and the information the the tooltip shown by hovering the question mark next to the plugin name.

### Troubleshooting

- Related to https://github.com/Crivella/ocr_extension/issues/5 If a plugins fails to install, either via an error message you see in the server window or by not having the models available, try the following:
  - Uninstall the plugin in question by deselecting it in the popup menu and clicking submit.
  - Nuke the entire plugin installation by:
    - Stopping the server
    - Delete the `plugins` directory and the `plugins.json` file under `$OCT_BASE_DIR` (default to `$HOME/.ocr_translate` on Linux and `%userprofile%\.ocr_translate` on Windows)
    - Restart the server

If all else fails, please open an issue on the [backend server](https://github.com/Crivella/ocr_translate) possibly attaching the DEBUG log of the server (run the server by setting the environment variable `DJANGO_LOG_LEVEL=DEBUG` in your `run-user.[sh/bat]` script).

## Possible problems

- [Issue 25](/../../issues/25) Using uBlock origin (or possibly other extension capable of blocking content) could stop the extension from sending requests to the server. This can be recognized if the popup for setting the language and models works fine but then the translations fails without producing any new log in the server windows. (WIP long term fix in the extension)

- [Issue 27](/../../issues/27) Having non latin characters in the model's path can cause HuggingFace `transformers` to fail loading them
