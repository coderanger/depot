# coding=utf8
import bz2
import collections
import os
import re
import tarfile
import time

try:
    import lzma
except ImportError:
    lzma = None

import arpy
import six

from .utils import gzip_compress
from .version import __version__


class AptMeta(collections.OrderedDict):
    def __init__(self, data):
        super(AptMeta, self).__init__()
        self._data = data  # For testing/debugging
        last_key = None
        for line in data.splitlines() if hasattr(data, 'splitlines') else data.readlines():
            line = line.rstrip('\n')
            if line[0].isspace():
                if last_key:
                    self[last_key] += '\n' + line
                else:
                    raise ValueError('Can not parse line: {0}'.format(repr(line)))
            else:
                last_key, value = line.split(':', 1)
                value = value.lstrip(' ')
                self[last_key] = value

    def __str__(self):
        return '\n'.join('{0}:{1}{2}'.format(key, '' if value[0] == '\n' else ' ', value) for key, value in six.iteritems(self) if value)


class AptPackage(AptMeta):
    def __init__(self, filename, fileobj=None, data=None):
        self.name = filename
        if not data:
            if fileobj:
                self.ar = arpy.Archive(filename or getattr(fileobj, 'name', None), fileobj)
            else:
                self.ar = arpy.Archive(filename)
            self.ar.read_all_headers()
            self.control_tar = tarfile.open('control.tar.gz', 'r:gz', fileobj=self.ar.archived_files['control.tar.gz'])
            data = self.control_tar.extractfile('./control')
        super(AptPackage, self).__init__(data)

    @property
    def pool_path(self):
        filename = self.name or self['Filename']
        return 'pool/{0}'.format(os.path.basename(filename))


class AptPackages(object):
    def __init__(self, storage, data):
        self.storage = storage
        self.packages = {}
        self._data = data  # For testing/debugging
        for buf in data.split('\n\n'):
            if not buf.strip():
                continue
            pkg = AptPackage(None, data=buf)
            self.packages[(pkg['Package'], pkg['Version'])] = pkg

    def add(self, pkg):
        hashes = self.storage.hashes(pkg.pool_path)
        pkg['Filename'] = pkg.pool_path
        pkg['Size'] = str(hashes['size'].size)
        pkg['MD5sum'] = hashes['md5'].hexdigest()
        pkg['SHA1'] = hashes['sha1'].hexdigest()
        pkg['SHA256'] = hashes['sha256'].hexdigest()
        self.packages[(pkg['Package'], pkg['Version'])] = pkg

    def __str__(self, extra_fn=None):
        return '\n\n'.join(str(pkg) for key, pkg in sorted(six.iteritems(self.packages), key=lambda k: k[0]))


class AptRelease(AptMeta):
    def __init__(self, storage, codename, *args, **kwargs):
        self.storage = storage
        self.codename = codename
        super(AptRelease, self).__init__(*args, **kwargs)
        if 'Components' not in self:
            # Need to setup some defaults
            self['Origin'] = 'Depot {0}'.format(__version__)
            self['Date'] = ''  # Will be regenerated, but lock the order
            self['Codename'] = self.codename
            # These are filled in using add_metadata()
            self['Architectures'] = ''
            self['Components'] = ''

        self.hashes = {
            'md5': self._parse_hashes('MD5Sum'),
            'sha1': self._parse_hashes('SHA1'),
            'sha256': self._parse_hashes('SHA256'),
        }

    def _parse_hashes(self, key):
        hashes = collections.OrderedDict()
        if key in self:
            for line in self[key].splitlines():
                line = line.strip()
                if not line:
                    continue
                hash, size, path = line.split(' ', 2)
                hashes[path] = (hash, size)
        return hashes

    def _compile_hashes(self, key):
        return '\n' + '\n'.join(' {0} {1} {2}'.format(hash, size, path) for path, (hash, size) in six.iteritems(self.hashes[key]))

    def update_hash(self, path):
        hashes = self.storage.hashes('dists/{0}/{1}'.format(self.codename, path))
        for hash_type in list(six.iterkeys(self.hashes)):
            self.hashes[hash_type][path] = (hashes[hash_type].hexdigest(), str(hashes['size'].size))

    def add_metadata(self, component, architecture):
        components = set(s for s in self['Components'].split() if s)
        components.add(component)
        self['Components'] = ' '.join(sorted(components))
        architectures = set(s for s in self['Architectures'].split() if s)
        architectures.add(architecture)
        self['Architectures'] = ' '.join(sorted(architectures))

    def __str__(self):
        self['MD5Sum'] = self._compile_hashes('md5')
        self['SHA1'] = self._compile_hashes('sha1')
        self['SHA256'] = self._compile_hashes('sha256')
        if not self.get('Date'):
            now = time.gmtime()
            # The debian standard (Policy 4.4) really does specify the English labels
            day_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][now.tm_wday]
            month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][now.tm_mon - 1]
            self['Date'] = time.strftime('{0}, %d {1} %Y %H:%M:%S UTC'.format(day_of_week, month), now)
        return super(AptRelease, self).__str__()


class AptRepository(object):
    # ex. mypgk@1.0
    COPY_SPEC_RE = re.compile(r'^([\w_-]+)@(.+?)$')

    def __init__(self, storage, gpg, codename, component='main', architecture=None):
        self.storage = storage
        self.gpg = gpg
        self.codename = codename
        self.component = component
        self.architecture = architecture
        self.dirty_packages = {}  # arch: [pkg,+]
        self.dirty_sources = False

    def add_package(self, path, fileobj=None, force=False):
        fileobj = fileobj or open(path, 'rb')
        path = os.path.basename(path)
        pkg = AptPackage(path, fileobj)
        # Check that we have an arch if needed
        arch = pkg['Architecture']
        if pkg['Architecture'] == 'any':
            arch = self.architecture
            if not arch:
                raise ValueError('Architechture required when adding packages for "any"')

        # Check that the package doesn't already exist
        if not force and pkg.pool_path in self.storage:
            return False

        # Stream up the actual package file
        fileobj.seek(0, 0)
        self.storage.upload(pkg.pool_path, fileobj)
        self.dirty_packages.setdefault(arch, []).append(pkg)
        return True

    def copy_package(self, package):
        md = self.COPY_SPEC_RE.match(package)
        if not md:
            raise ValueError('Unable to parse {0)'.format(repr(package)))
        #package_name = md.group(1)
        #package_version = md.group(2)
        #package_component = md.group(3)
        raise NotImplementedError('TODO finish this')

    def commit_package_metadata(self, arch, pkgs):
        # Update the Packages file
        packages_path = 'dists/{0}/{1}/binary-{2}/Packages'.format(self.codename, self.component, arch)
        packages = AptPackages(self.storage, self.storage.download(packages_path, skip_hash=True) or '')
        for pkg in pkgs:
            packages.add(pkg)
        packages_raw = str(packages)
        self.storage.upload(packages_path, packages_raw)
        self.storage.upload(packages_path+'.gz', gzip_compress(packages_raw))
        self.storage.upload(packages_path+'.bz2', bz2.compress(packages_raw))
        if lzma:
            self.storage.upload(packages_path+'.lzma', lzma.compress(packages_raw))

    def commit_sources_metadata(self):
        # Update the Sources file
        sources_path = 'dists/{0}/{1}/source/Sources'.format(self.codename, self.component)
        if sources_path in self.storage:
            return
        sources_content = ''
        self.storage.upload(sources_path, sources_content)
        self.storage.upload(sources_path+'.gz', gzip_compress(sources_content))
        self.storage.upload(sources_path+'.bz2', bz2.compress(sources_content))
        if lzma:
            self.storage.upload(sources_path+'.lzma', lzma.compress(sources_content))
        self.dirty_sources = True

    def commit_release_metadata(self, archs):
        # Update Release
        release_path = 'dists/{0}/Release'.format(self.codename)
        release = AptRelease(self.storage, self.codename, self.storage.download(release_path, skip_hash=True) or '')
        for arch in archs:
            release.add_metadata(self.component, arch)
            release_packages_path = '{0}/binary-{1}/Packages'.format(self.component, arch)
            release.update_hash(release_packages_path)
            release.update_hash(release_packages_path+'.gz')
            release.update_hash(release_packages_path+'.bz2')
            if lzma:
                release.update_hash(release_packages_path+'.lzma')
        if self.dirty_sources:
            release_sources_path = '{0}/source/Sources'.format(self.component)
            release.update_hash(release_sources_path)
            release.update_hash(release_sources_path+'.gz')
            release.update_hash(release_sources_path+'.bz2')
            if lzma:
                release.update_hash(release_sources_path+'.lzma')
        # Force the date to regenerate
        release['Date'] = None
        release_raw = str(release)
        self.storage.upload(release_path, release_raw)

        # GPG signing
        if self.gpg:
            # Fun fact, even debian's own tools don't seem to support this InRelease file
            in_release_path = 'dists/{0}/InRelease'.format(self.codename)
            self.storage.upload(in_release_path, self.gpg.sign(release_raw))
            self.storage.upload(release_path+'.gpg', self.gpg.sign(release_raw, detach=True))

            # Upload the pubkey to be nice
            self.storage.upload('pubkey.gpg', self.gpg.public_key())

    def commit_metadata(self):
        for arch, packages in six.iteritems(self.dirty_packages):
            self.commit_package_metadata(arch, packages)
        self.commit_sources_metadata()
        self.commit_release_metadata(six.iterkeys(self.dirty_packages))
