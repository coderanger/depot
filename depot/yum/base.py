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

import collections

from defusedxml import lxml
from lxml.builder import ElementMaker
from lxml.etree import QName
import six


class YumMeta(collections.OrderedDict):
    nsmap = {}

    def __init__(self, *args, **kwargs):
        self.filename = kwargs.pop('filename') if 'filename' in kwargs else None
        super(YumMeta, self).__init__(*args, **kwargs)

    @classmethod
    def from_file(cls, filename=None, fileobj=None, *args, **kwargs):
        fileobj = fileobj or open(filename, 'rb')
        kwargs['filename'] = filename
        kwargs['root'] = lxml.parse(fileobj)
        return cls.from_element(*args, **kwargs)

    @classmethod
    def from_element(cls, root, *args, **kwargs):
        raise NotImplementedError

    def to_element(self, E):
        raise NotImplementedError

    def encode(self):
        return lxml.tostring(
            self.to_element(ElementMaker(nsmap=self.nsmap)),
            xml_declaration=True,
            encoding='UTF-8',
        )


class YumData(collections.OrderedDict):
    NS = None
    # Sentinel object
    NoInsert = object()

    @classmethod
    def from_element(cls, root):
        self = cls(**cls.root_from_element(root))
        for elm in root.findall('*'):
            key = QName(elm.tag).localname
            fn = getattr(self, '{0}_from_element'.format(key.replace('-', '_')), None)
            val = fn(key, elm) if fn else elm.text
            if val is not self.NoInsert:
                self[key] = val
        return self

    @classmethod
    def root_from_element(cls, root):
        return root.attrib

    def to_element(self, E):
        sub = []
        for key, value in six.iteritems(self):
            ns_key = '{{{0}}}{1}'.format(self.NS, key) if self.NS else key
            fn = getattr(self, '{0}_to_element'.format(key.replace('-', '_')), None)
            if fn:
                elm = fn(E, ns_key, value)
            elif value:
                elm = E(ns_key, value)
            else:
                elm = E(ns_key)
            sub.append(elm)
        return self.root_to_element(E, sub)

    def root_to_element(self, E, sub):
        return E.data(*sub)
