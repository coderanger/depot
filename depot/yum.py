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
    def from_element(cls, root):
        self = cls(root.attrib['type'])
        for elm in root.findall('*'):
            self[QName(elm.tag).localname] = elm.attrib.get('href', elm.text)
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


class YumRepoMD(collections.OrderedDict):
    DataClass = YumRepoMDData

    def __init__(self, revision=0, tags=None, *args, **kwargs):
        super(YumRepoMD, self).__init__(*args, **kwargs)
        self.revision = revision
        self.tags = tags or []

    @classmethod
    def from_file(cls, filename, fileobj=None):
        fileobj = fileobj or open(filename, 'rb')
        return cls.from_element(lxml.parse(fileobj))

    @classmethod
    def from_element(cls, root):
        self = cls(
            revision=int(root.find('{*}revision').text),
            tags=[elm.text for elm in root.findall('{*}tags/{*}content')],
        )
        for elm in root.findall('{*}data'):
            data = self.DataClass.from_element(elm)
            self[data.type] = data
        return self

    def to_element(self, E):
        return E.repomd(
            E.revision(str(self.revision)),
            E.tags(*[E.content(tag) for tag in self.tags]),
            *[data.to_element(E) for data in six.itervalues(self)]
        )

    def __str__(self):
        nsmap = {
            None: 'http://linux.duke.edu/metadata/repo',
            'rpm': 'http://linux.duke.edu/metadata/rpm',
        }
        E = ElementMaker(nsmap=nsmap)
        return '<?xml version="1.0" ?>\n' + lxml.tostring(self.to_element(E), encoding=unicode).encode('utf-8')
