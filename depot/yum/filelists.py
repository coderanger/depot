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


class YumFileListsPackage(YumData):
    def __init__(self, pkgid, name, arch, *args, **kwargs):
        super(YumFileListsPackage, self).__init__(*args, **kwargs)
        self.pkgid = pkgid
        self.name = name
        self.arch = arch
        self.files = []

    def version_from_element(self, key, elm):
        return elm.attrib

    def file_from_element(self, key, elm):
        self.files.append((elm.attrib.get('type'), elm.text))
        return self.NoInsert

    def version_to_element(self, E, key, value):
        elm = E(key)
        for a_key, a_value in six.iteritems(value):
            elm.attrib[a_key] = a_value
        return elm

    def root_to_element(self, E, sub):
        for file_type, file_path in self.files:
            elm = E.file(file_path)
            if file_type:
                elm.attrib['type'] = file_type
            sub.append(elm)
        root = E.package(*sub)
        root.attrib['pkgid'] = self.pkgid
        root.attrib['name'] = self.name
        root.attrib['arch'] = self.arch
        return root


class YumFileLists(YumMeta):
    PackageClass = YumFileListsPackage
    nsmap = {None: 'http://linux.duke.edu/metadata/filelists'}

    @classmethod
    def from_element(cls, root, *args, **kwargs):
        self = cls(*args, **kwargs)
        for elm in root.findall('{*}package'):
            pkg = self.PackageClass.from_element(elm)
            self[pkg.pkgid] = pkg  # Should this be a (name, arch, ver) tuple like YumPrimary?
        return self

    def to_element(self, E):
        return E.filelists(*[pkg.to_element(E) for pkg in six.itervalues(self)], packages=str(len(self)))
