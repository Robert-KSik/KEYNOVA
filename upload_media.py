"""
ONE-TIME helper: uploads the photos in your local media/ folder to Cloudinary.

Photo names stay exactly the same, so the records you copied to the live
database keep working without any changes. Safe to run more than once.

How to run (from the project folder, with .venv active). In PowerShell:

    $env:DATABASE_URL   = "postgresql://...your live database..."
    $env:CLOUDINARY_URL = "cloudinary://API_KEY:API_SECRET@CLOUD_NAME"

    python upload_media.py --dry-run     # shows what it WOULD upload
    python upload_media.py               # does the upload

Close the terminal afterwards so those two values are forgotten.
"""
import os
import sys
from pathlib import Path

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.apps import apps
from django.conf import settings
from django.db import models

if not os.environ.get("CLOUDINARY_URL"):
    sys.exit("CLOUDINARY_URL is not set in this terminal. Nothing uploaded.")

import cloudinary.uploader  # noqa: E402  (needs CLOUDINARY_URL first)

dry_run = "--dry-run" in sys.argv
media_root = Path(settings.MEDIA_ROOT)

uploaded = 0
missing = 0
renamed = 0

for model in apps.get_models():
    for field in model._meta.get_fields():
        if not (
            isinstance(field, models.FileField)
            and getattr(field, "concrete", False)
        ):
            continue

        for obj in model.objects.all():
            name = getattr(obj, field.name).name

            if not name:
                continue

            label = f"{model.__name__}#{obj.pk}.{field.name}"
            path = media_root / name

            if not path.is_file():
                print(f"  MISSING  {label}: {name} (not in your media folder)")
                missing += 1
                continue

            root, ext = os.path.splitext(name.replace("\\", "/"))
            new_name = f"{root}{ext.lower()}"

            if dry_run:
                print(f"  would upload  {label}: {name}")
                uploaded += 1
                continue

            cloudinary.uploader.upload(
                str(path),
                public_id=root,
                resource_type="image",
                overwrite=True,
            )

            # Cloudinary links use a lower-case extension.
            if new_name != name:
                model.objects.filter(pk=obj.pk).update(**{field.name: new_name})
                renamed += 1

            print(f"  uploaded  {label}: {name}")
            uploaded += 1

print()
print(f"{'Would upload' if dry_run else 'Uploaded'}: {uploaded}")
print(f"Missing files: {missing}")
if renamed:
    print(f"Names fixed to lower-case extension: {renamed}")