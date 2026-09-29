import hashlib
import io
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import repackage


class PackagingBoundary(unittest.TestCase):
    def test_rejects_unreviewed_archive_before_signing(self):
        with tempfile.TemporaryDirectory() as tmp, patch('subprocess.run') as signer:
            root = Path(tmp)
            (root / 'arm64.tgz').write_bytes(b'unreviewed')
            with self.assertRaisesRegex(ValueError, 'checksum mismatch'):
                repackage.repackage(root, root / 'out', 'A' * 40, root / 'license')
            signer.assert_not_called()

    def test_rejects_link_even_if_archive_hash_matches(self):
        with tempfile.TemporaryDirectory() as tmp, patch('subprocess.run') as signer:
            root = Path(tmp)
            archive = root / 'arm64.tgz'
            with tarfile.open(archive, 'w:gz') as tar:
                entry = tarfile.TarInfo('doctl')
                entry.type, entry.linkname = tarfile.SYMTYPE, '/bin/sh'
                tar.addfile(entry)
            with patch.dict(repackage.INPUTS, {'arm64': hashlib.sha256(archive.read_bytes()).hexdigest()}):
                with self.assertRaisesRegex(ValueError, 'regular doctl'):
                    repackage.repackage(root, root / 'out', 'A' * 40, root / 'license')
            signer.assert_not_called()


if __name__ == '__main__':
    unittest.main()
