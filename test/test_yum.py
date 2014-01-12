import os
import re

import pytest
from pretend import call_recorder, call, stub

from depot.yum import YumRepoMD, YumPrimary

# Convert XML into a format that diffs nicely
def unify_spacing(data):
    return re.sub('>', '>\n', re.sub('\s+', ' ', re.sub('>', '>\n', re.sub('\n', '', data))))

class TestYumRepoMD(object):
    @pytest.fixture
    def epel(self):
        return YumRepoMD.from_file(os.path.join(os.path.dirname(__file__), 'data', 'epel_repomd.xml'))

    @pytest.fixture
    def pgdg(self):
        return YumRepoMD.from_file(os.path.join(os.path.dirname(__file__), 'data', 'pgdg_repomd.xml'))

    def test_from_file(self, epel):
        assert epel.revision == 1389466441
        assert epel.tags == ['binary-i386']
        assert epel['filelists']['checksum'] == '8892c3e34eef269cea677558ee5a40057052ecff'
        assert epel['filelists']['open-checksum'] == 'b6081d9789bf5cef2ffac8c03fa67224b8c22f53'
        assert epel['group']['location'] == 'repodata/fdddf90da3a700ad6da5ff78e13c17258655bbe3-comps-el5.xml'

    def test_str_epel(self, epel):
        raw = open(os.path.join(os.path.dirname(__file__), 'data', 'epel_repomd.xml'), 'rb').read()
        assert unify_spacing(str(epel)) == unify_spacing(raw)

    def test_str_pgdg(self, pgdg):
        raw = open(os.path.join(os.path.dirname(__file__), 'data', 'pgdg_repomd.xml'), 'rb').read()
        assert unify_spacing(str(pgdg)) == unify_spacing(raw)


class TestYumPrimary(object):
    @pytest.fixture
    def epel(self):
        return YumPrimary.from_file(os.path.join(os.path.dirname(__file__), 'data', 'epel_primary.xml'))

    @pytest.fixture
    def pgdg(self):
        return YumPrimary.from_file(os.path.join(os.path.dirname(__file__), 'data', 'pgdg_primary.xml'))

    @pytest.fixture
    def pgdgmini(self):
        return YumPrimary.from_file(os.path.join(os.path.dirname(__file__), 'data', 'pgdgmini_primary.xml'))

    def test_from_file_pgdgmini(self, pgdgmini):
        assert pgdgmini[('ip4r93', 'x86_64', '0:1.05-3.rhel6')]['summary'] == 'IPv4 and IPv4 range index types for PostgreSQL'
        assert pgdgmini[('ip4r93', 'x86_64', '0:1.05-3.rhel6')]['url'] == 'http://pgfoundry.org/projects/ip4r'
        assert pgdgmini[('postgresql93-debuginfo', 'x86_64', '0:9.3.1-1PGDG.rhel6')]['checksum'] == '048be8c5573c0d92bf64e476beb739c31b2d0f91'
        assert pgdgmini[('postgresql93-debuginfo', 'x86_64', '0:9.3.1-1PGDG.rhel6')]['url'] == ''


    def test_str_epel(self, epel):
      raw = open(os.path.join(os.path.dirname(__file__), 'data', 'epel_primary.xml'), 'rb').read()
      assert unify_spacing(str(epel)) == unify_spacing(raw)

    def test_str_pgdg(self, pgdg):
      raw = open(os.path.join(os.path.dirname(__file__), 'data', 'pgdg_primary.xml'), 'rb').read()
      assert unify_spacing(str(pgdg)) == unify_spacing(raw)

    def test_str_pgdgmini(self, pgdgmini):
        path = os.path.join(os.path.dirname(__file__), 'data', 'pgdgmini_primary.xml')
        raw = open(path, 'rb').read()
        assert unify_spacing(str(pgdgmini)) == unify_spacing(raw)

