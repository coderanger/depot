import getpass
import os

import gnupg


class GPG(object):
    def __init__(self, keyid):
        self.gpg = gnupg.GPG(use_agent=False)
        self.keyid = keyid
        if not self.keyid:
            # Compat with how Freight does it.
            self.keyid = os.environ.get('GPG')
        self.passphrase = None
        self._verify()

    def _verify(self):
        """Some sanity checks on GPG."""
        if not self.keyid:
            raise ValueError('No GPG key specified for signing, did you mean to use --no-sign?')
        sign = self.gpg.sign('', keyid=self.keyid)
        if 'secret key not available' in sign.stderr:
            raise ValueError('Key not found')
        elif 'NEED_PASSPHRASE' in sign.stderr:
            self.passphrase = getpass.getpass('Passphrase for GPG key: ')

    def sign(self, data, detach=False):
        sign = self.gpg.sign(data, keyid=self.keyid, passphrase=self.passphrase, detach=detach)
        if not sign:
            raise ValueError(sign.stderr)
        return str(sign)

    def public_key(self):
        return self.gpg.export_keys(self.keyid)
