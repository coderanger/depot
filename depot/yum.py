import collections

from defusedxml import lxml
from lxml.builder import ElementMaker
from lxml.etree import QName
import six

class YumMeta(collections.OrderedDict):
    nsmap = {}

    @classmethod
    def from_file(cls, filename, fileobj=None):
        fileobj = fileobj or open(filename, 'rb')
        return cls.from_element(lxml.parse(fileobj))

    @classmethod
    def from_element(cls, root):
        raise NotImplementedError

    def to_element(self, E):
        raise NotImplementedError

    def __str__(self):
        return lxml.tostring(
            self.to_element(ElementMaker(nsmap=self.nsmap)),
            xml_declaration=True,
            encoding='UTF-8')


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
        sub = [E.revision(str(self.revision))]
        if self.tags:
            sub.append(E.tags(*[E.content(tag) for tag in self.tags]))
        for data in six.itervalues(self):
            sub.append(data.to_element(E))
        return E.repomd(*sub)


class YumPrimaryFormat(collections.OrderedDict):
    def __init__(self, *args, **kwargs):
        super(YumPrimaryFormat, self).__init__(*args, **kwargs)
        self.files = []

    @classmethod
    def from_element(cls, root):
        self = cls()
        for elm in root.findall('*'):
            key = QName(elm.tag).localname
            if key == 'header-range':
                self[key] = elm.attrib
            elif key == 'provides' or key == 'requires' or key == 'conflicts' or key == 'obsoletes':
                self[key] = [entry.attrib for entry in elm.findall('{*}entry')]
            elif key == 'file':
                self.files.append((elm.attrib.get('type'), elm.text))
            else:
                self[key] = elm.text
        return self

    def to_element(self, E):
        sub = []
        for key, value in six.iteritems(self):
            ns_key = '{{http://linux.duke.edu/metadata/rpm}}{0}'.format(key)
            if key == 'header-range':
                elm = E(ns_key)
                for a_key, a_value in six.iteritems(value):
                    elm.attrib[a_key] = a_value
            elif key == 'provides' or key == 'requires' or key == 'conflicts' or key == 'obsoletes':
                entries = []
                for entry in value:
                    e_elm = E('{http://linux.duke.edu/metadata/rpm}entry')
                    for e_key, e_value in six.iteritems(entry):
                        e_elm.attrib[e_key] = e_value
                    entries.append(e_elm)
                if not entries:
                    entries.append('')
                elm = E(ns_key, *entries)
            elif value:
                elm = E(ns_key, value)
            else:
                elm = E(ns_key)
            sub.append(elm)
        for file_type, file_path in self.files:
            elm = E.file(file_path)
            if file_type:
                elm.attrib['type'] = file_type
            sub.append(elm)
        return E.format(*sub)


class YumPrimaryPackage(collections.OrderedDict):
    FormatClass = YumPrimaryFormat

    def __init__(self, type, *args, **kwargs):
        super(YumPrimaryPackage, self).__init__(*args, **kwargs)
        self.type = type

    @classmethod
    def from_element(cls, root):
        self = cls(root.attrib['type'])
        for elm in root.findall('*'):
            key = QName(elm.tag).localname
            if key == 'version' or key == 'time' or key == 'size':
                self[key] = elm.attrib
            elif key == 'location':
                self[key] = elm.attrib['href']
            elif key == 'format':
                self[key] = self.FormatClass.from_element(elm)
            else:
                self[key] = elm.text
        return self

    def full_version(self):
        return '{epoch}:{ver}={rel}'.format(**self['version'])

    def to_element(self, E):
        sub = []
        for key, value in six.iteritems(self):
            if key == 'version' or key == 'time' or key == 'size':
                elm = E(key)
                for a_key, a_value in six.iteritems(value):
                    elm.attrib[a_key] = a_value
            elif key == 'location':
                elm = E.location(href=value)
            elif key == 'checksum':
                elm = E.checksum(value)
                elm.attrib['type'] = 'sha'
                elm.attrib['pkgid'] = 'YES'
            elif key == 'format':
                elm = value.to_element(E)
            else:
                elm = E(key, value or '')
            sub.append(elm)
        return E.package(*sub, type=self.type)


class YumPrimary(YumMeta):
    PackageClass = YumPrimaryPackage
    nsmap = {
        None: 'http://linux.duke.edu/metadata/common',
        'rpm': 'http://linux.duke.edu/metadata/rpm',
    }

    @classmethod
    def from_element(cls, root):
        self = cls()
        for elm in root.findall('{*}package'):
            pkg = self.PackageClass.from_element(elm)
            self[(pkg['name'], pkg['arch'], pkg.full_version())] = pkg
        return self

    def to_element(self, E):
        return E.metadata(*[pkg.to_element(E) for pkg in six.itervalues(self)], packages=str(len(self)))
