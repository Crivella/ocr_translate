# Change Log

List of changes between versions

## 0.2.0

Restructured the code to make it pluginable.
No change should be noticeable from a user experience point of view, but now it should be much easier to contribute to the code (new functionalities can be introduced by writing a plugin without having to modify this codebase).

- The models entries in the database now requires an `entrypoint` field to identify which model should be used to load it.
- The functionality related to `easyocr`, `tesseract` and `hugginface` models have been moved to the `ocr_translate/plugins` folder, and are now plugins (kept in the main codebase to leave an example on how a plugin can work).

## 0.1.4
