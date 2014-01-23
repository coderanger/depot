import os
import hashlib

import pytest
from pretend import call_recorder, call, stub

from depot.apt import AptPackages, AptRelease, AptRepository

def fixture_path(*path):
    return os.path.join(os.path.dirname(__file__), 'data', *path)

@pytest.fixture
def storage():
    return stub(
        hashes=call_recorder(lambda path: {'size': stub(size=1), 'sha1': hashlib.sha1(), 'sha256': hashlib.sha256(), 'md5': hashlib.md5()}),
        __contains__=lambda key: False,
        upload=lambda path, fileobj: None,
    )

class TestAptPackages(object):
    @pytest.fixture
    def pgdg(self, storage):
        data = open(os.path.join(os.path.dirname(__file__), 'data', 'pgdg_Packages'), 'rb').read()
        return AptPackages(storage, data)

    def test_reading(self, pgdg):
        # Check that the keys match
        packages = sorted(['libecpg-compat2', 'libecpg-dev', 'libecpg5', 'libpgtypes2', 'libpq-dev', 'libpq5'])
        assert sorted(pgdg.packages.keys()) == [(p, '8.2.23-1.pgdg12.4+1') for p in packages]
        # Just testing a few random keys since an exhaustive test would be too verbose
        assert pgdg.packages[('libecpg-compat2', '8.2.23-1.pgdg12.4+1')]['Filename'] == 'pool/8.2/p/postgresql-8.2/libecpg-compat2_8.2.23-1.pgdg12.4+1_amd64.deb'
        assert pgdg.packages[('libpgtypes2', '8.2.23-1.pgdg12.4+1')]['SHA256'] == 'bc711ca44adfc4425e69a1777c4284ac942b3f352d8296a3047895e97d82489b'
        assert pgdg.packages[('libpq-dev', '8.2.23-1.pgdg12.4+1')]['Description'] == '''header files for libpq5 (PostgreSQL library)
 Header files and static library for compiling C programs to link
 with the libpq library in order to communicate with a PostgreSQL
 database backend.
 .
 PostgreSQL is an object-relational SQL database management system.'''

    def test_adding(self, pgdg):
        package_data = {'Package': 'test', 'Version': '1'}
        package = stub(pool_path='pool/main/t/test/test.deb', __getitem__=package_data.__getitem__, __setitem__=package_data.__setitem__)
        pgdg.add(package)
        assert pgdg.packages[('test', '1')]['Filename'] == 'pool/main/t/test/test.deb'
        assert pgdg.packages[('test', '1')]['Size'] == '1'
        assert pgdg.packages[('test', '1')]['SHA1'] == 'da39a3ee5e6b4b0d3255bfef95601890afd80709'

    def test_serializing(self, pgdg):
        assert str(pgdg).strip() == pgdg._data.strip()


class TestAptRelease(object):
    @pytest.fixture
    def pgdg(self, storage):
        data = open(os.path.join(os.path.dirname(__file__), 'data', 'pgdg_Release'), 'rb').read()
        return AptRelease(storage, 'precise-pgdg', data)

    def test_reading(self, pgdg):
        assert pgdg['Architectures'] == 'amd64 i386'
        assert pgdg['Date'] == 'Mon, 30 Dec 2013 17:34:01 UTC'

    def test_reading_hashes(self, pgdg):
        assert pgdg.hashes['md5']['8.3/source/Release'] == ('0ca3534d616a6a902c6ed3877d30e740', '132')

    def test_serializing(self, pgdg):
        assert str(pgdg).strip() == pgdg._data.strip()

    def test_add_metadata(self, pgdg):
        assert pgdg['Components'] == 'main 8.2 8.3 8.4 9.0 9.1 9.2 9.3'
        assert pgdg['Architectures'] == 'amd64 i386'
        pgdg.add_metadata('test', 'amd64')
        assert pgdg['Components'] == '8.2 8.3 8.4 9.0 9.1 9.2 9.3 main test'
        assert pgdg['Architectures'] == 'amd64 i386'
        pgdg.add_metadata('test', 'test')
        assert pgdg['Components'] == '8.2 8.3 8.4 9.0 9.1 9.2 9.3 main test'
        assert pgdg['Architectures'] == 'amd64 i386 test'

    def test_update_hash(self, pgdg):
        pgdg.update_hash('main/binary-amd64/Packages')
        assert pgdg.storage.hashes.calls == [call('dists/precise-pgdg/main/binary-amd64/Packages')]
        assert pgdg.hashes['md5']['main/binary-amd64/Packages'] == ('d41d8cd98f00b204e9800998ecf8427e', '1')
        assert pgdg.hashes['sha1']['main/binary-amd64/Packages'] == ('da39a3ee5e6b4b0d3255bfef95601890afd80709', '1')
        assert pgdg.hashes['sha256']['main/binary-amd64/Packages'] == ('e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855', '1')

class TestAptRepository(object):
    @pytest.fixture
    def package_path(self):
        return fixture_path('depot_1.2.3-1_amd64.deb')

    def test_duplicate_upload(self, storage, package_path):
        storage.__contains__ = lambda key: True
        repo = AptRepository(storage, None, None)
        assert not repo.add_package(package_path)

    def test_duplicate_upload_force(self, storage, package_path):
        storage.__contains__ = lambda key: True
        repo = AptRepository(storage, None, None)
        assert repo.add_package(package_path, force=True)

    def test_nonduplicate_upload(self, storage, package_path):
        repo = AptRepository(storage, None, None)
        assert repo.add_package(package_path, force=True)
