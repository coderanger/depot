import zlib

from depot.apt import AptPackage, AptPackages

class Repository(object):
    def __init__(self, storage):
        self.storage = storage

    def create(self):
        raise NotImplementedError

    def add_package(self, path):
        raise NotImplementedError

    def remove_package(self, package_id):
        raise NotImplementedError


class AptRepository(Repository):
    def add_package(self, path, codename, component='main', arch=None):
        pkg = AptPackage(path)
        # Check that we have an arch if needed
        if pkg['architecture'] == 'any':
            if not arch:
                raise ValueError('Architechture required when adding packages for "any"')
        else:
            arch = pkg['architecture']

        # Stream up the actual package file
        self.storage.upload(pkg.pool_path, open(path, 'rb'))

        # Update the Packages file
        packages_path = 'dists/{0}/{1}/binary-{2}/Packages'.format(codename, component, arch)
        packages = AptPackages(self.storage.download(packages_path, skip_hash=True) or '')
        packages.add(pkg, self.storage.hashes(pkg.pool_path))
        packages_raw = str(packages)
        self.storage.upload(packages_path, packages_raw)
        self.storage.upload(packages_path+'.gz', zlib.compress(packages_raw))

        # Update
