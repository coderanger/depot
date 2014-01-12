import os
import re

import pytest
from pretend import call_recorder, call, stub

from depot.yum import YumRepoMD

class TestYumRepoMD(object):
  @pytest.fixture
  def epel(self):
    return YumRepoMD.from_file(os.path.join(os.path.dirname(__file__), 'data', 'epel_repomd.xml'))

  def test_from_file(self, epel):
    assert epel.revision == 1389466441
    assert epel.tags == ['binary-i386']
    assert epel['filelists']['checksum'] == '8892c3e34eef269cea677558ee5a40057052ecff'
    assert epel['filelists']['open-checksum'] == 'b6081d9789bf5cef2ffac8c03fa67224b8c22f53'
    assert epel['group']['location'] == 'repodata/fdddf90da3a700ad6da5ff78e13c17258655bbe3-comps-el5.xml'

  def test_str(self, epel):
    raw = open(os.path.join(os.path.dirname(__file__), 'data', 'epel_repomd.xml'), 'rb').read()
    def unify_spacing(data):
      return re.sub('>', '>\n', re.sub('\s+', ' ', re.sub('>', '>\n', re.sub('\n', '', data))))
    assert unify_spacing(str(epel)) == unify_spacing(raw)
