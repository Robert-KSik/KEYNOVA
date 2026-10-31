"""
Stores uploaded files (product photos, payment screenshots) on Cloudinary.

Used automatically when the CLOUDINARY_URL environment variable is set
(see STORAGES in settings.py). Without it, Django keeps using the local
media/ folder.

CLOUDINARY_URL looks like:  cloudinary://API_KEY:API_SECRET@CLOUD_NAME
(copy it from your Cloudinary dashboard).
"""
import os
import uuid
from urllib.parse import quote

import cloudinary
import cloudinary.uploader
from django.core.files.base import ContentFile
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from django.utils.text import get_valid_filename


@deconstructible
class CloudinaryMediaStorage(Storage):
    """Minimal Django storage backend for image uploads."""

    @staticmethod
    def _public_id(name):
        return os.path.splitext(name)[0]

    def exists(self, name):
        # Every saved file gets a random suffix (see _save), so a new
        # upload can never collide with an existing one.
        return False

    def _save(self, name, content):
        folder, filename = os.path.split(name.replace("\\", "/"))
        root, ext = os.path.splitext(get_valid_filename(filename))

        # Keep the stored name short enough for the database column
        root = root[:50] or "file"
        unique_root = f"{root}_{uuid.uuid4().hex[:8]}"
        public_id = f"{folder}/{unique_root}" if folder else unique_root

        content.seek(0)
        cloudinary.uploader.upload(
            content.read(),
            public_id=public_id,
            resource_type="image",
            overwrite=False,
        )

        return f"{public_id}{ext.lower()}"

    def url(self, name):
        cloud_name = cloudinary.config().cloud_name
        return (
            f"https://res.cloudinary.com/{cloud_name}"
            f"/image/upload/{quote(name)}"
        )

    def delete(self, name):
        try:
            cloudinary.uploader.destroy(
                self._public_id(name),
                resource_type="image",
                invalidate=True,
            )
        except Exception:
            # Never let a failed cleanup break the page the user is on.
            pass

    def _open(self, name, mode="rb"):
        import urllib.request

        with urllib.request.urlopen(self.url(name)) as response:
            return ContentFile(response.read(), name=name)