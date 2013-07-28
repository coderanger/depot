import hashlib
import os
from urlparse import urlparse

import six
import libcloud.security
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError

# Include the current cURL CA bundle as a fallback
_base_path = os.path.abspath(os.path.dirname(__file__))
libcloud.security.CA_CERTS_PATH.append(os.path.join(_base_path, 'cacert.pem'))

class Sizer(object):
    def __init__(self):
        self.size = 0

    def update(self, data):
        self.size += len(data)


class StorageWrapper(object):
    def __init__(self, uri, no_public=False):
        self.uri = uri = urlparse(uri)
        self.no_public = no_public
        self.storage = self._get_storage(self.uri)
        self._hashes = {}

    def upload(self, path, data):
        if isinstance(data, basestring):
            # Simple case of in-memory content
            return self.upload(path, (data,))
        elif hasattr(data, 'read'):
            # File-like object
            def it(size=4096):
                buf = data.read(size)
                while buf:
                    yield buf
                    buf = data.read(size)
            return self.upload(path, it())
        else:
            # Just try iterating
            self._update_hashes(path, '')
            path_root, path_ext = os.path.splitext(path)
            extra = {}
            if path_ext == '.gz':
                extra['content_type'] = 'application/x-gzip'
            else:
                extra['content_type'] = 'text/plain'
            if not self.no_public:
                if self.uri.scheme.startswith('s3'):
                    # Yeah so this doesn't work, scroll down to the bottom and cry
                    extra['meta_data'] = {'acl': 'public-read'}
                # Other clouds here
            return self.storage.upload_object_via_stream((self._update_hashes(path, buf, False) for buf in data), path, extra=extra)

    def download(self, path, skip_hash=False):
        # Assumption, this isn't a big file
        try:
            obj = self.storage.get_object(path)
        except ObjectDoesNotExistError:
            return None
        if not skip_hash:
            self._update_hashes(path, '')
        return ''.join(
            buf if skip_hash else self._update_hashes(path, buf, False)
            for buf in self.storage.download_object_as_stream(obj)
        )

    def __contains__(self, path):
        try:
            self.storage.get_object(path)
            return True
        except ObjectDoesNotExistError:
            return False

    def _update_hashes(self, path, data, reset=True):
        if reset or path not in self._hashes:
            self._hashes[path] = {
                'md5': hashlib.md5(),
                'sha1': hashlib.sha1(),
                'sha256': hashlib.sha256(),
                'size': Sizer(),
            }
        if data:
            for hasher in six.itervalues(self._hashes[path]):
                hasher.update(data)
        return data

    def hashes(self, path):
        if path not in self._hashes:
            self._update_hashes(path, '')
        return self._hashes[path]

    @staticmethod
    def _get_storage(uri):
        """
        Given a URI like local:///srv/repo or s3://key:secret/apt.example.com,
        return a libcloud storage or container object.
        """
        driver = get_driver(uri.scheme)
        key = uri.username
        secret = uri.password
        container = uri.netloc
        if uri.scheme.startswith('s3'):
            if not key:
                key = os.environ.get('AWS_ACCESS_KEY_ID')
            if not secret:
                secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
            if not (key and secret and container):
                raise ValueError('For S3 you must provide an access key ID, secret access key, and bucket name')
        elif uri.scheme == 'local':
            parts = []
            if uri.netloc:
                parts.append(uri.netloc)
            if uri.path:
                parts.append(uri.path)
            if not parts:
                parts.append('.')
            base_path = os.path.abspath(''.join(parts))
            key = os.path.dirname(base_path)
            container = os.path.basename(base_path)
        storage = driver(key, secret)
        try:
            return storage.get_container(container)
        except ContainerDoesNotExistError:
            return storage.create_container(container)


# OH GOD I DON'T EVEN
from libcloud.storage.drivers.s3 import S3StorageDriver
old_upload_object = S3StorageDriver._upload_object
def _upload_object(*args, **kwargs):
    if 'headers' in kwargs:
        kwargs['headers']['x-amz-acl'] = 'public-read'
    return old_upload_object(*args, **kwargs)
S3StorageDriver._upload_object = _upload_object
