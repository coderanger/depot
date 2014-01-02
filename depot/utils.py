import cStringIO
import gzip

def gzip_compress(data):
    gz_data = cStringIO.StringIO()
    gz = gzip.GzipFile('Packages', 'wb', fileobj=gz_data)
    gz.write(data)
    gz.close()
    return gz_data.getvalue()
