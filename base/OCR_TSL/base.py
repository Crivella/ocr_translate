import json
from pathlib import Path

from .. import models as m

# This should be set from env variables in the container
root = Path("C:\models")
root = Path("/home/crivella/app/AI")
dev = "cpu"

def import_models():
    with open(root / "config.json") as f:
        config = json.load(f)

    for name in config["ocr_models"]:
        m.OCRModel.objects.get_or_create(name=name)
    for name in config["tsl_models"]:
        m.TSLModel.objects.get_or_create(name=name)

    