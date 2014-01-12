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

import six

from .base import YumMeta, YumData


class YumRepoMDData(YumData):
    def __init__(self, type, *args, **kwargs):
        super(YumRepoMDData, self).__init__(*args, **kwargs)
        self.type = type

    def location_from_element(self, key, elm):
        return elm.attrib['href']

    def location_to_element(self, E, key, value):
        return E(key, href=value)

    def checksum_to_element(self, E, key, value):
        return E(key, value, type='sha')
    open_checksum_to_element = checksum_to_element

    def root_to_element(self, E, sub):
        return E.data(*sub, type=self.type)


class YumRepoMD(YumMeta):
    DataClass = YumRepoMDData
    nsmap = {
        None: 'http://linux.duke.edu/metadata/repo',
        'rpm': 'http://linux.duke.edu/metadata/rpm',
    }

    def __init__(self, revision=0, tags=None, *args, **kwargs):
        super(YumRepoMD, self).__init__(*args, **kwargs)
        self.revision = revision
        self.tags = tags or []

    @classmethod
    def from_element(cls, root, *args, **kwargs):
        kwargs['revision'] = int(root.find('{*}revision').text)
        kwargs['tags'] = [elm.text for elm in root.findall('{*}tags/{*}content')]
        self = cls(*args, **kwargs)
        for elm in root.findall('{*}data'):
            data = self.DataClass.from_element(elm)
            self[data.type] = data
        return self

    def to_element(self, E):
        sub = [E.revision(str(self.revision))]
        if self.tags:
            sub.append(E.tags(*[E.content(tag) for tag in self.tags]))
        for data in six.itervalues(self):
            sub.append(data.to_element(E))
        return E.repomd(*sub)
