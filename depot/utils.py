import cStringIO
import gzip


def gzip_compress(data, filename='<data>'):
    gz_data = cStringIO.StringIO()
    gz = gzip.GzipFile(filename, 'wb', fileobj=gz_data)
    gz.write(data)
    gz.close()
    return gz_data.getvalue()
