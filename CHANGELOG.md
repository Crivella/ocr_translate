# Change Log

List of changes between versions

## 0.2.1

Plugins can now be used to also add models to the database.
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
