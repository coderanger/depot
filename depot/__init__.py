"""Usage: depot [options] <package> [<package> ...]

-h --help                    show this help message and exit
--version                    show program's version number and exit
-s URI --storage=URI         URI for storage provider, checks $DEPOT_STORAGE or local://
-c NAME --codename=NAME      Debian distribution codename [default: lucid]
--component=NAME             Debian component name [default: main]
-a ARCH --architecture=ARCH  package architecture if not specified in package
-k KEYID --gpg-key=KEYID     GPG key ID to use for signing
--no-sign                    do not sign this upload
--no-public                  do not make cloud files public-readable

Example:
depot -s s3://apt.example.com -c precise -k 6791B14F mypackage.deb

"""

import os

import docopt
import six

from .apt import AptRepository
from .gpg import GPG
from .storage import StorageWrapper
from .version import __version_info__, __version__

def main():
    args = docopt.docopt(__doc__, version='depot '+__version__)
    if not args['--storage']:
        args['--storage'] = os.environ.get('DEPOT_STORAGE', 'local://')
    if args['--no-sign']:
        gpg = None
    else:
        gpg = GPG(args['--gpg-key'])
    storage = StorageWrapper(args['--storage'], args['--no-public'])
    repo = AptRepository(storage, gpg, args['--codename'], args['--component'], args['--architecture'])
    for pkg_path in args['<package>']:
        repo.add_package(pkg_path)
