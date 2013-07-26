Summary::

Used to push, it is a replacement for reprepro+s3cmd sync and whatnot.

It does incremental updates of a repo, so you don't need to keep a full local copy of the repo anymore.

You just feed it each package as they are made and it updates all the various metadata files as needed.

This was important since chef-server and private chef builds are like 300MB each, so keeping more than a few versions on disk on the build machines gets ugly


More later::

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
  
Example::
  depot -s s3://apt.example.com -c precise -k 6791B14F mypackage.deb
