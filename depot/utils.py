import gzip

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def gzip_compress(data, filename='<data>'):
    gz_data = StringIO()
    gz = gzip.GzipFile(filename, 'wb', fileobj=gz_data)
    gz.write(data)
    gz.close()
    return gz_data.getvalue()
