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
