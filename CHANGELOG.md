# Change Log

List of changes between versions

## XXX (maybe planned)

- [ ] Add null/passthrough OCR model (how should it be designed to report  both the boxes and the OCR step?)
- [ ] Possibly move to CUDA 12.9 and check if paddleocr can work also with the gpu version
- [ ] Add way to control server natively without the extension (e.g. through the admin page or another view)
- [ ] Make PMNG aware of manually installed plugins and gray them out in the extension
- [ ] Add <DETECT> language to allow either OCR or TSL models to detect the language automatically
      (Both should easy, only one could be troublesome)

## 0.7.1

- reflect bugfix in paddle plugin

## 0.7.0

### Breaking changes

- `staka/fugumt-...` models has been removed as it is not working with the newer dependencies.
  - Issue related to https://github.com/huggingface/transformers/issues/24657#issuecomment-3303054186
  - Unfortunately the version of transformers/tokenizers can't be lowered below `4.48.0/0.20.2`
    as tokenizers does not support python 3.13 before https://github.com/huggingface/tokenizers/releases/tag/v0.20.2

### Major Changes

- dependencies updates:
  - [X] `python`: support for `>=3.10, <=3.11` extended to `>=3.10` (will test `3.14` once it is out with all its prebuilt packages in PyPI)
  - [X] `CUDA`: from `11.8` updated to `12.8` (allow using `sm_120` GPUs like the RTX 5000 series)
  - [X] `torch`: from `2.2.1` updated to `2.8.0`
  - [X] `easyocr`: from `1.7.1` updated to `1.7.2`
  - [X] `paddleocr`: from `2.8.1` updated to `3.2.0`
    Different models and much ampler set of languages supported
- Improved logging of the server using [rich](https://github.com/Textualize/rich)
- Environment variables:
  - REMOVED:
    - `AUTO_CREATE_LANGUAGES` - Languages are now created once at first initialization if missing
      For now the languages have never changed across versions so it was never needed to recreate/updated them.
    - `AUTOCREATE_MODELS` - Models are now synchronized with the available entrypoints at every server start
      Removed models will be deactivated, and present models will be updated/created.
  - ADDED:
    - `OCT_LOGFILE` - `[true/false/path]`. If true, a logfile named `$OCT_BASE_DIR/ocr_translate.log` will be created. If a path is provided, that will be used instead.
- Logic of the `run_server.py` moved inside the package to improve testing and modularity (the script will appear much smaller in the release)
- QoL improvements for manual plugins installations
  - If you want to try your own plugins or you want to manually install the supported ones (eg with modifications) you can now do so by installing them in the server
    environment.
  - The server will automatically pick up the plugin module name and add it to the DJANGO apps, and synchronize the models in the database at launch.
  - **NOTE**: packages coming from the managed plugins will take precedence over manually installed ones. This could cause package conflicts. Mix stuff at your own risk.

### Fixes

- Fix #55

## 0.6.3

Changes

- Bumped version of `ocr_translate_ollama` plugin to `0.2.0` in order to allow using newer versions of `ollama` (> 0.5.5)


## 0.6.2

Changes

- Added capability to use `django-cors-headers` to set CORS headers in server responses
- Added capability to set `CSRF_TRUSTED_ORIGINS` to make admin interface properly work from a docker container
- Documented new environment variables

Fixes:

- Fix #45 (Mishandling of empty string environment variables in run_server.py)

## 0.6.1

- Ensure changing an option for only a step of the pipeline will not cause the other steps to also be re-triggered
  (Unless there is some change in the incoming input from a changed step)
- Added locks to API to avoid loading/using models while plugin_manager is working.
- `plugin_manager` will try to reinstall failed packages 3 times with an interval before failing
- Added capability to load both MOST or LAST model used at server start (Fixes #42) \
  `LOAD_ON_START` can now be set to either `most` or `last` to load the most used or the last used model at server start.
  Setting it to `true` will default to `most` with a deprecation warning.
- Added 2 environment variables to control server update behavior:
  - `OCT_VERSION` = (`[current_number]/latest`) - The version to install/update to default to the version of the downloaded release.
    If set to `latest` the server will attempt to update to the latest version.
    Can be set to any number of version available on PyPI https://pypi.org/project/django-ocr_translate/#history
  - `OCT_AUTOUPDATE` = (`[false]/true`) - If set to `true` the server will attempt to upgrade the version at every start
    to the configured value of `OCT_VERSION` (default is release version).

## 0.6.0

### IMPORTANT

From version 0.6 onward `python` and `pip` need to be installed on the system.
See more below in the [Changes](#changes) section.

- Windows: https://www.python.org/downloads/windows/
  - **NOTE**: make sure to check the box that says "Add Python to PATH" so that pip can be found by the server script without having to make any assumptions

- Linux: Use your package manager (e.g. `sudo apt install python3 python3-pip`)

### Changes

- Removed the frozen executable from the release files in favor of an Automatic1111 stile batch script
  - Even with the plugin manager, installing some dependencies that requiers actual compilation by invoking pip from within the frozen executable was giving non trivial to fix trouble.\
    For this reason I decided to axe the PyInstaller frozen EXE all together and go with a batch script that will:
    - Allow user to more easily set environment variables (a few of the most relevant ones are already set as empty in the script)
    - Create or reuse a virtual environment in a folder `venv` in the same directory as the script
    - Install the minimum required packages in it to run the server
    - Run the server
- Added a plugin manager to install/uninstall plugins on demand
  - The installed plugins can be controlled via the new version of the firefox extension or directly using the
    `manage_plugins/` endpoint.
  - The plugins will by be installed under `$OCT_BASE_DIR/plugins` which by default will be under your user profile (e.g. `C:\Users\username\.ocr_translate` on windows). \
    If you have trouble with space under `C:\` consider setting the `OCT_BASE_DIR` environment variable to a different location.
  - The plugin data is stored in a JSON file inside the project [plugins_data.json](blob/v0.6.0/ocr_translate/plugins_data.json)
  - Version/Scope/Extras of a package to be installed can be controlled via environment variables

        OCT_PKG_<package_name(uppercase)>_[VERSION|SCOPE|EXTRAS]

    (eg to change torch to version A.B.C you would set `OCT_PKG_TORCH_VERSION="A.B.C"`).
    If the package name contains a `-` it should be replaced with `_min_` in the package name
  - Removed env variable `AUTOCREATE_VALIDATED_MODELS` and relative server initialization.
    Now models are created/activated or deactivated via the plugin manager, when the respective plugin is installed/uninstalled.
- Streamlined docker image to also use the `run_server.py` script for initialization.
- Added plugin for `ollama` (https://github.com/ollama/ollama) for translation using LLMs
  - Note ollama needs to be run/installed separately and the plugin will just make calls to the server.
  - Use the `OCT_OLLAMA_ENDPOINT` environment variable to specify the endpoint of the ollama server
    ([see the plugin page for more details](https://github.com/Crivella/ocr_translate-ollama))
- Added plugin for `PaddleOCR` (https://github.com/PaddlePaddle/PaddleOCR) (Box and OCR) (seems to work very well
  with chinese).
  - The default versions installed by the `plugin_manager` of `paddlepaddle` (`2.5.2` on linux and `2.6.1` on windows)
    might not work for every system as there can be underlying failures in the C++ code that the plugin uses.
    The version installed can be controlled using the environment variable `OCT_PKG_PADDLEPADDLE_VERSION`.
- Added possibility to specify extra `DJANGO_ALLOWED_HOSTS` and a server bind address via environment variables. (Fixes #30)
- Manual model is not implemented as an entrypoint anymore (will work also without recreating models).
- OCR models can now use a `tokenizer` and a `processor` from different models.
- Added caching of the languages and allowed box/ocr/tsl models for faster response times on the handshake endpoint.
- New endpoint `run_tsl_xua` made to work with `XUnity.AutoTranslator` (https://github.com/bbepis/XUnity.AutoTranslator)
- Improved API return codes

## 0.5.1

- Implemented endpoint for manual translation
- Added autocorrect capability to Trie
- Added endpoint for sending allowed options given the loaded models
- Improved admin interface to allow users to more easily add models to the database
- Changed handshake endpoint behavior to send more information required by the extension
- Improved run_server script for better modularity and reporting
- Minor fixes

## 0.4.0

Now it is possible to use OCR models that work on a single line.
Before the pipeline would pass the entire BOX to the OCR model which would make model trained on single line spit out nonsensical results.
Now model can be created with `ocr_mode` sto to `merged`[default] or `single`.
If set to single the non-merged bounding boxes will be passed and the model will afterward stich the text back together by reasonably ordering the Boxes by line/column chunks.

- Modified the API for the `OCRBoxModel._box_detection` should now return a list of dictionaries containing `'merged: tuple[int, int, int, int]` the merged bounding box and `'single': list[tuple[int, int, int, int]]` a list of single bounding boxes that has been merged into `merged`.
- Modified the database models:
  - `OCRModel`: Added `ocr_mode` field with possible values: `merged`[default] `single`.
  - `BBox`: Foreign key `from_ocr` renamed to `from_ocr_merged`
  - `BBox`: Added foreign key `from_ocr_single`
  - `BBox`: Added foreign key `to_merged` (point to the merged `BBox` generated by merging THIS + other boxes)
  - `OCRRun`: Foreign key `result` renamed to `result_merged` (denote the output was from a merged real/mock run)
  - `OCRRun`: Added foreign key `result_single` (denote the output was from a single run)
- Fixed a bug related to Issue #11 where the `%userprofile%/.ocr_translate` folder was not being properly created by the EXE release if it did not exists.

## 0.3.2

restore_missing_spaces with no trie (None for that language) was causing exceptions.
Now the server will skip this step if the trie for the selected language is not found.

## 0.3.1

Removed runaway print statements

## 0.3.0

- All feature for box/ocr/tsl have been moved to plugins in separate packages
- Improved pre-parsing of OCRed text for languages with latin alphabet
  - Introduced a way to remove ghost carachter generated at the begin/end of every string
  - Introduced Trie capability
    - Can use trie to detect if an incorrect work ("helloworld") should be split into multiple valid words (["hello", "world"])
  - Added English word list/freq file.

## 0.2.1

Plugins can now be used to also add models to the database via the following entrypoints:

- `ocr_translate.box_data`
- `ocr_translate.ocr_data`
- `ocr_translate.tsl_data`

The entrypoint should point to a `dict` with the info to create the model.
See [init of plugins](ocr_translate/plugins/__init__.py) for example (care that box/ocr/tsl may need to define different keys).

Information about model-specific language codes is now encoded into an `iso1_map` field of the model.

- Before new models with custom codes in a plugin would require to also edit the main repo and adding a new column to languages in the database.
- Now the plugin can set the `lang_code` to whatever is closest to the model codes, and overwrite what does not match using `iso1_map`, by mapping iso-639-1 codes to the model-specific ones.

Tag only without release as the changes still requires plugins to be baked in with the installer (they cannot be dynamically added without an hack-ish solution).

## 0.2.0

Restructured the code to make it pluginable.
No change should be noticeable from a user experience point of view, but now it should be much easier to contribute to the code (new functionalities can be introduced by writing a plugin without having to modify this codebase).

- The models entries in the database now requires an `entrypoint` field to identify which model should be used to load it.
- The functionality related to `easyocr`, `tesseract` and `hugginface` models have been moved to the `ocr_translate/plugins` folder, and are now plugins (kept in the main codebase to leave an example on how a plugin can work).

## 0.1.4
