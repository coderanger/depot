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

from depot.yum import YumRepoMD, YumPrimary, YumFileLists


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
        raw = open(epel.filename, 'rb').read()
        assert unify_spacing(str(epel)) == unify_spacing(raw)

    def test_str_pgdg(self, pgdg):
        raw = open(pgdg.filename, 'rb').read()
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
        raw = open(epel.filename, 'rb').read()
        assert unify_spacing(str(epel)) == unify_spacing(raw)

    def test_str_pgdg(self, pgdg):
        raw = open(pgdg.filename, 'rb').read()
        assert unify_spacing(str(pgdg)) == unify_spacing(raw)

    def test_str_pgdgmini(self, pgdgmini):
        raw = open(pgdgmini.filename, 'rb').read()
        assert unify_spacing(str(pgdgmini)) == unify_spacing(raw)


class TestYumFileLists(object):
    @pytest.fixture
    def epel(self):
        path = os.path.join(os.path.dirname(__file__), 'data', 'epel_filelists.xml.gz')
        gz = gzip.open(path, 'rb')
        epel =  YumFileLists.from_file(path, fileobj=gz)
        epel._gz = gz
        return epel

    @pytest.fixture
    def pgdg(self):
        return YumFileLists.from_file(os.path.join(os.path.dirname(__file__), 'data', 'pgdg_filelists.xml'))

    def test_str_epel(self, epel):
        epel._gz.rewind()
        raw = epel._gz.read()
        assert unify_spacing(str(epel)) == unify_spacing(raw)

    def test_str_pgdg(self, pgdg):
        raw = open(pgdg.filename, 'rb').read()
        assert unify_spacing(str(pgdg)) == unify_spacing(raw)

