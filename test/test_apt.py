import os
import hashlib

import pytest
from pretend import stub

from depot.apt import AptPackages

class TestAptPackages(object):
    @pytest.fixture
    def pgdg(self):
        storage = stub(hashes=lambda path: {'size': stub(size=1), 'sha1': hashlib.sha1(), 'sha256': hashlib.sha256(), 'md5': hashlib.md5()})
        data = open(os.path.join(os.path.dirname(__file__), 'data', 'pgdg_Packages'), 'rb').read()
        packages = AptPackages(storage, data)
        packages._data = data
        return packages

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
