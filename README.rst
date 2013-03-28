More later:

Usage: depot [options] <package> [<package> ...]

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
