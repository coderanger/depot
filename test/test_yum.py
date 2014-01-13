#
# Author:: Noah Kantrowitz <noah@coderanger.net>
#
# Copyright 2014, Noah Kantrowitz
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import gzip
import os
import re

import pytest
import six

from depot.yum import YumRepoMD, YumPrimary, YumFileLists, YumOther


# Convert XML into a format that diffs nicely
def unify_spacing(data):
    if not isinstance(data, six.binary_type):
        data._fileobj.seek(0, 0)
        data = data._fileobj.read()
    return re.sub('>', '>\n', re.sub('\s+', ' ', re.sub('>', '>\n', re.sub('\n', '', data))))

def fixture(cls, name):
    path = os.path.join(os.path.dirname(__file__), 'data', name)
    open_ = gzip.open if path.endswith('.gz') else open
    fileobj = open_(path, 'rb')
    obj =  cls.from_file(path, fileobj=fileobj)
    obj._fileobj = fileobj
    return obj


class TestYumRepoMD(object):
    @pytest.fixture
    def epel(self):
        return fixture(YumRepoMD, 'epel_repomd.xml')

    @pytest.fixture
    def pgdg(self):
        return fixture(YumRepoMD, 'pgdg_repomd.xml')

    def test_from_file(self, epel):
        assert epel.revision == 1389466441
        assert epel.tags == ['binary-i386']
        assert epel['filelists']['checksum'] == '8892c3e34eef269cea677558ee5a40057052ecff'
        assert epel['filelists']['open-checksum'] == 'b6081d9789bf5cef2ffac8c03fa67224b8c22f53'
        assert epel['group']['location'] == 'repodata/fdddf90da3a700ad6da5ff78e13c17258655bbe3-comps-el5.xml'

    def test_str_epel(self, epel):
        assert unify_spacing(epel.encode()) == unify_spacing(epel)

    def test_str_pgdg(self, pgdg):
        assert unify_spacing(pgdg.encode()) == unify_spacing(pgdg)


class TestYumPrimary(object):
    @pytest.fixture
    def epel(self):
        return fixture(YumPrimary, 'epel_primary.xml.gz')

    @pytest.fixture
    def pgdg(self):
        return fixture(YumPrimary, 'pgdg_primary.xml')

    @pytest.fixture
    def pgdgmini(self):
        return fixture(YumPrimary, 'pgdgmini_primary.xml')

    def test_from_file_pgdgmini(self, pgdgmini):
        assert pgdgmini[('ip4r93', 'x86_64', '0:1.05-3.rhel6')]['summary'] == 'IPv4 and IPv4 range index types for PostgreSQL'
        assert pgdgmini[('ip4r93', 'x86_64', '0:1.05-3.rhel6')]['url'] == 'http://pgfoundry.org/projects/ip4r'
        assert pgdgmini[('postgresql93-debuginfo', 'x86_64', '0:9.3.1-1PGDG.rhel6')]['checksum'] == '048be8c5573c0d92bf64e476beb739c31b2d0f91'
        assert pgdgmini[('postgresql93-debuginfo', 'x86_64', '0:9.3.1-1PGDG.rhel6')]['url'] == ''

    def test_str_epel(self, epel):
        assert unify_spacing(epel.encode()) == unify_spacing(epel)

    def test_str_pgdg(self, pgdg):
        assert unify_spacing(pgdg.encode()) == unify_spacing(pgdg)

    def test_str_pgdgmini(self, pgdgmini):
        assert unify_spacing(pgdgmini.encode()) == unify_spacing(pgdgmini)


class TestYumFileLists(object):
    @pytest.fixture
    def epel(self):
        return fixture(YumFileLists, 'epel_filelists.xml.gz')

    @pytest.fixture
    def pgdg(self):
        return fixture(YumFileLists, 'pgdg_filelists.xml')

    def test_str_epel(self, epel):
        assert unify_spacing(epel.encode()) == unify_spacing(epel)

    def test_str_pgdg(self, pgdg):
        assert unify_spacing(pgdg.encode()) == unify_spacing(pgdg)


class TestYumOther(object):
    @pytest.fixture
    def epel(self):
        return fixture(YumOther, 'epel_other.xml.gz')

    @pytest.fixture
    def pgdg(self):
        return fixture(YumOther, 'pgdg_other.xml')

    def test_str_epel(self, epel):
        assert unify_spacing(epel.encode()) == unify_spacing(epel)

    def test_str_pgdg(self, pgdg):
        assert unify_spacing(pgdg.encode()) == unify_spacing(pgdg)
