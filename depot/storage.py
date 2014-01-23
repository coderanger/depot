import hashlib
import os
import tempfile

import six
import libcloud.security
from libcloud.storage.providers import get_driver
from libcloud.storage.types import ContainerDoesNotExistError, ObjectDoesNotExistError
from six.moves.urllib.parse import urlparse

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
        self.uri = urlparse(uri)
        self.no_public = no_public
        self.storage = self._get_storage(self.uri)
        self._hashes = {}

    def upload(self, path, data):
        if isinstance(data, six.binary_type):
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
                    extra['acl'] = 'public-read'
                # Other clouds here
            return self.storage.upload_object_via_stream((self._update_hashes(path, buf, False) for buf in data), path, extra=extra)

    def download(self, path, skip_hash=False):
        # Assumption, this isn't a big file
        it = self.download_iter(path, skip_hash)
        if it:
            return ''.join(it)

    def download_iter(self, path, skip_hash=False):
        try:
            obj = self.storage.get_object(path)
        except ObjectDoesNotExistError:
            return None
        if not skip_hash:
            self._update_hashes(path, '')
        return (
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

    @classmethod
    def file(cls, uri_or_path):
        """
        Given either a URI like s3://bucket/path.txt or a path like /path.txt,
        return a file object for it.
        """
        uri = urlparse(uri_or_path)
        if not uri.scheme:
            # Just a normal path
            return open(uri_or_path, 'rb')
        else:
            it = cls(uri_or_path).download_iter(uri.path.lstrip('/'), skip_hash=True)
            if not it:
                raise ValueError('{0} not found'.format(uri_or_path))
            tmp = tempfile.TemporaryFile()
            for chunk in it:
                tmp.write(chunk)
            tmp.seek(0, 0)
            return tmp

    @classmethod
    def _get_storage(cls, uri):
        """
        Given a URI like local:///srv/repo or s3://key:secret@apt.example.com,
        return a libcloud storage or container object.
        """
        driver = cls._get_driver(uri.scheme)
        key = uri.username
        secret = uri.password
        container = uri.netloc
        driver_kwargs = {}
        if uri.scheme.startswith('s3'):
            if not key:
                key = os.environ.get('AWS_ACCESS_KEY_ID')
            if not secret:
                secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
            if not (key and secret and container):
                raise ValueError('For S3 you must provide an access key ID, secret access key, and bucket name')
            # No way to store this in the URI, what about a CLI option too?
            if 'AWS_TOKEN' in os.environ:
                driver_kwargs['token'] = os.environ['AWS_TOKEN']
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
        storage = driver(key, secret, **driver_kwargs)
        try:
            return storage.get_container(container)
        except ContainerDoesNotExistError:
            return storage.create_container(container)

    @classmethod
    def _get_driver(cls, name):
        """Wrapper for libcloud's get_driver for testing."""
        return get_driver(name)
