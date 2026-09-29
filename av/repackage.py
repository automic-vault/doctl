#!/usr/bin/env python3
"""Sign the pinned upstream doctl release without patching executable code."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

VERSION = '1.175.0'
RELEASE = VERSION + '-av.1'
TEAM = 'ZU76A67LGU'
INPUTS = {
    'arm64': '68493d57c3868e23ad1abdffa01977314c3d9b12b5cfcfdc1db924c8b81a5924',
    'amd64': '167eb4474e864e07fa3a04e9ab5feb94812e64d993299e81831cdfb34f91cc25',
}
REQUIREMENT = ('identifier "doctl" and anchor apple generic and '
               'certificate 1[field.1.2.840.113635.100.6.2.6] exists and '
               'certificate leaf[field.1.2.840.113635.100.6.1.13] exists and '
               f'certificate leaf[subject.OU] = "{TEAM}"')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def repackage(inputs, output, identity, license_path):
    if not re.fullmatch(r'[A-Fa-f0-9]{40}', identity):
        raise ValueError('Use the certificate fingerprint of the release signing identity')
    output.mkdir(parents=True, exist_ok=True)
    manifest = {'upstream_version': VERSION, 'release': RELEASE, 'artifacts': {}}
    for arch, expected in INPUTS.items():
        archive = inputs / f'{arch}.tgz'
        if digest(archive.read_bytes()) != expected:
            raise ValueError(f'{arch}: upstream archive checksum mismatch')
        with tempfile.TemporaryDirectory() as tmp:
            binary = Path(tmp) / 'doctl'
            with tarfile.open(archive) as tar:
                members = tar.getmembers()
                if len(members) != 1 or members[0].name != 'doctl' or not members[0].isfile() or not 0 < members[0].size <= 64*1024*1024:
                    raise ValueError('Expected only a bounded regular doctl executable')
                binary.write_bytes(tar.extractfile(members[0]).read())
            binary.chmod(0o755)
            subprocess.run(['/usr/bin/codesign', '--force', '--sign', identity,
                            '--identifier', 'doctl', '--options', 'runtime', '--timestamp', str(binary)], check=True)
            subprocess.run(['/usr/bin/codesign', '--verify', '--strict', '-R', '=' + REQUIREMENT, str(binary)], check=True)
            posture = subprocess.check_output(['/usr/bin/codesign', '-dvv', str(binary)], stderr=subprocess.STDOUT).decode()
            if 'runtime' not in posture or f'TeamIdentifier={TEAM}' not in posture:
                raise ValueError('Wrong signing team or missing Hardened Runtime')
            entitlements = subprocess.check_output(['/usr/bin/codesign', '-d', '--entitlements', ':-', str(binary)], stderr=subprocess.DEVNULL)
            if entitlements.strip():
                raise ValueError('No runtime exception entitlements are permitted')
            data = binary.read_bytes()
            name = f'doctl-{RELEASE}-darwin-{arch}.tar.gz'
            target = output / name
            # Timestamped CMS signatures are intentionally not reproducible. AV pins the actual output.
            with target.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0) as zipped, tarfile.open(fileobj=zipped, mode='w') as tar:
                for member_name, contents, mode in [('doctl', data, 0o755), ('LICENSE.txt', license_path.read_bytes(), 0o644)]:
                    entry = tarfile.TarInfo(member_name)
                    entry.size, entry.mode = len(contents), mode
                    tar.addfile(entry, io.BytesIO(contents))
            manifest['artifacts'][arch] = {'name': name, 'archive_sha256': digest(target.read_bytes()), 'binary_sha256': digest(data), 'upstream_archive_sha256': expected}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--inputs', type=Path, required=True, help='arm64.tgz and amd64.tgz from digitalocean/doctl v1.175.0')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--license', type=Path, default=Path(__file__).resolve().parents[1] / 'LICENSE.txt')
    args = parser.parse_args()
    repackage(args.inputs, args.output, args.identity, args.license)
