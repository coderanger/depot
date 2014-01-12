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

  def test_str_epel(self, epel):
    raw = open(os.path.join(os.path.dirname(__file__), 'data', 'epel_primary.xml'), 'rb').read()
    assert unify_spacing(str(epel)) == unify_spacing(raw)

  def test_str_pgdg(self, pgdg):
    raw = open(os.path.join(os.path.dirname(__file__), 'data', 'pgdg_primary.xml'), 'rb').read()
    assert unify_spacing(str(pgdg)) == unify_spacing(raw)

  def test_str_pgdgmini(self):
    path = os.path.join(os.path.dirname(__file__), 'data', 'pgdgmini_primary.xml')
    pgdg = YumPrimary.from_file(path)
    raw = open(path, 'rb').read()
    assert unify_spacing(str(pgdg)) == unify_spacing(raw)

