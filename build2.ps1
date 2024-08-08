# This should be ran inside a virtualenv where only `django-ocr_translate` has been installed with
# `pip install django-ocr_translate[release]`

$env:DJANGO_SETTINGS_MODULE="mysite.settings"
$env:OCT_DISABLE_PLUGINS="1"

pyinstaller `
    --onedir `
    --name run_server `
    --icon icon.ico `
    --add-data "ocr_translate/ocr_tsl/languages.json:ocr_translate/ocr_tsl" `
    --add-data "ocr_translate/plugins_data.json:ocr_translate" `
    --add-data "ocr_translate/dictionaries/*:ocr_translate/dictionaries" `
    --hidden-import pickletools `
    --collect-all unittest `
    --collect-all pickle `
    --collect-all filecmp `
    --collect-all modulefinder `
    --collect-all logging `
    --collect-all timeit `
    --collect-all cProfile `
    --collect-all PIL `
    --collect-all opencv-contrib-python `
    --collect-all setuptools `
    --collect-all wave `
    --collect-all cgi `
    --collect-all imghdr `
    run_server.py
