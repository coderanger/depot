import collections

from defusedxml import lxml
from lxml.builder import ElementMaker
from lxml.etree import QName
import six

class YumRepoMDData(collections.OrderedDict):
    def __init__(self, type, *args, **kwargs):
        super(YumRepoMDData, self).__init__(*args, **kwargs)
        self.type = type

    @classmethod
    def from_element(cls, elm):
        self = cls(elm.attrib['type'])
        for sub in elm.findall('*'):
            self[QName(sub.tag).localname] = sub.attrib.get('href', sub.text)
        return self

    def to_element(self, E):
        sub = []
        for key, value in six.iteritems(self):
            if key == 'location':
                elm = E.location(href=value)
            elif key == 'checksum' or key == 'open-checksum':
                elm = E(key, value, type='sha')
            else:
                elm = E(key, value)
            sub.append(elm)
        return E.data(*sub, type=self.type)


class YumRepoMD(object):
    def __init__(self):
        self.revision = 0
        self.tags = []
        self.data = collections.OrderedDict()

    @classmethod
    def from_file(cls, filename, fileobj=None):
        fileobj = fileobj or open(filename, 'rb')
        root = lxml.parse(fileobj)
        self = cls()
        self.revision = int(root.find('{*}revision').text)
        self.tags = [elm.text for elm in root.findall('{*}tags/{*}content')]
        for elm in root.findall('{*}data'):
            data = YumRepoMDData.from_element(elm)
            self.data[data.type] = data
        return self

    def __getitem__(self, key):
        return self.data[key]

    def __str__(self):
        nsmap = {
            None: 'http://linux.duke.edu/metadata/repo',
            'rpm': 'http://linux.duke.edu/metadata/rpm',
        }
        E = ElementMaker(nsmap=nsmap)
        root = E.repomd(
            E.revision(str(self.revision)),
            E.tags(*[E.content(tag) for tag in self.tags]),
            *[data.to_element(E) for data in six.itervalues(self.data)]
        )
        return '<?xml version="1.0" ?>\n' + lxml.tostring(root, encoding=unicode).encode('utf-8')
