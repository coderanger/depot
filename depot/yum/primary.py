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


class YumPrimaryFormat(YumData):
    NS = 'http://linux.duke.edu/metadata/rpm'

    def __init__(self, *args, **kwargs):
        super(YumPrimaryFormat, self).__init__(*args, **kwargs)
        self.files = []

    def header_range_from_element(self, key, elm):
        return elm.attrib

    def provides_from_element(self, key, elm):
        return [entry.attrib for entry in elm.findall('{*}entry')]
    requires_from_element = provides_from_element
    conflicts_from_element = provides_from_element
    obsoletes_from_element = provides_from_element

    def file_from_element(self, key, elm):
        self.files.append((elm.attrib.get('type'), elm.text))
        return self.NoInsert

    def vendor_from_element(self, key, elm):
        return elm.text or ''

    def header_range_to_element(self, E, key, value):
        elm = E(key)
        for a_key, a_value in six.iteritems(value):
            elm.attrib[a_key] = a_value
        return elm

    def provides_to_element(self, E, key, value):
        entries = []
        for entry in value:
            e_elm = E('{{{0}}}entry'.format(self.NS))
            for e_key, e_value in six.iteritems(entry):
                e_elm.attrib[e_key] = e_value
            entries.append(e_elm)
        if not entries:
            entries.append('')
        return E(key, *entries)
    requires_to_element = provides_to_element
    conflicts_to_element = provides_to_element
    obsoletes_to_element = provides_to_element

    def root_to_element(self, E, sub):
        for file_type, file_path in self.files:
            elm = E.file(file_path)
            if file_type:
                elm.attrib['type'] = file_type
            sub.append(elm)
        return E.format(*sub)


class YumPrimaryPackage(YumData):
    FormatClass = YumPrimaryFormat

    def __init__(self, type, *args, **kwargs):
        super(YumPrimaryPackage, self).__init__(*args, **kwargs)
        self.type = type

    def location_from_element(self, key, elm):
        return elm.attrib['href']

    def version_from_element(self, key, elm):
        return elm.attrib
    time_from_element = version_from_element
    size_from_element = version_from_element

    def format_from_element(self, key, elm):
        return self.FormatClass.from_element(elm)

    def packager_from_element(self, key, elm):
        return elm.text or ''
    url_from_element = packager_from_element

    def location_to_element(self, E, key, value):
        return E(key, href=value)

    def version_to_element(self, E, key, value):
        elm = E(key)
        for a_key, a_value in six.iteritems(value):
            elm.attrib[a_key] = a_value
        return elm
    time_to_element = version_to_element
    size_to_element = version_to_element

    def checksum_to_element(self, E, key, value):
        elm = E(key, value)
        elm.attrib['type'] = 'sha'
        elm.attrib['pkgid'] = 'YES'
        return elm

    def format_to_element(self, E, key, value):
        return value.to_element(E)

    def packager_to_element(self, E, key, value):
        return E(key, value or '')
    url_to_element = packager_to_element

    def root_to_element(self, E, sub):
        return E.package(*sub, type=self.type)

    def full_version(self):
        return '{epoch}:{ver}-{rel}'.format(**self['version'])


class YumPrimary(YumMeta):
    PackageClass = YumPrimaryPackage
    nsmap = {
        None: 'http://linux.duke.edu/metadata/common',
        'rpm': 'http://linux.duke.edu/metadata/rpm',
    }

    @classmethod
    def from_element(cls, root, *args, **kwargs):
        self = cls(*args, **kwargs)
        for elm in root.findall('{*}package'):
            pkg = self.PackageClass.from_element(elm)
            self[(pkg['name'], pkg['arch'], pkg.full_version())] = pkg
        return self

    def to_element(self, E):
        return E.metadata(*[pkg.to_element(E) for pkg in six.itervalues(self)], packages=str(len(self)))
