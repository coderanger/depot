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

import os

from depot.storage import StorageWrapper

class TestStorage(object):
    def test_file_abspath(self):
        fileobj = StorageWrapper.file(__file__)
        assert isinstance(fileobj, file)

    def test_file_relpath(self):
        cwd = os.getcwd()
        try:
            os.chdir(os.path.dirname(__file__))
            fileobj = StorageWrapper.file('test_storage.py')
            assert isinstance(fileobj, file)
        finally:
            os.chdir(cwd)

    def test_file_uri(self):
        # Should really just poke the dummy driver here instead
        class StorageWrapperTest(StorageWrapper):
            def download_iter(self, path, *args, **kwargs):
                return (path,)
        fileobj = StorageWrapperTest.file('dummy://bucket/path/to/txt')
        assert isinstance(fileobj, file)
        assert fileobj.read() == 'path/to/txt'
