# user_messages/storages_backends.py
from storages.backends.s3boto3 import S3Boto3Storage

class MediaStorage(S3Boto3Storage):
    location = 'media'
    file_overwrite = False
    default_acl = None

    def get_object_parameters(self, name):
        return {
            "ContentType": self._guess_content_type(name),
            "ContentDisposition": "inline",
            "CacheControl": "max-age=86400",
        }

    def _guess_content_type(self, name):
        import mimetypes
        content_type, _ = mimetypes.guess_type(name)
        return content_type or "application/octet-stream"