#!/usr/bin/env python3
"""GPL-3.0 repack of a pinned, verified official DiPlay APK.

Only the Android binary manifest and JAR signing metadata are changed.
The original DEX, resources, native libraries and runtime assets are preserved.
Signing keys are created locally; never commit the signing-local directory.
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
import pathlib
import re
import secrets
import shutil
import struct
import subprocess
import urllib.request
import zipfile

BASE = pathlib.Path(__file__).resolve().parent
OLD_PACKAGE = 'com.shihab.diplay.cn'
NEW_PACKAGE = OLD_PACKAGE + '.landscape'
LABEL = 'DiPlay 横屏修正版'
VERSION = '0.2.17-cn.2-landscape.2'
ORIENTATION = 8  # reverseLandscape, fixed to the opposite landscape edge.
OFFICIAL_SHA256 = '4d80bbdce45f52353fe8695efd5d777911aff53f6adc761f5266b675490c70de'
OFFICIAL_URL = 'https://github.com/serein-morii/DiPlay-CN/releases/download/v0.2.17-cn.2/DiPlay-cn-v0.2.17-cn.2.apk'
SIGNATURE = re.compile(r'^META-INF/(?:MANIFEST\.MF|[^/]+\.(?:SF|RSA|DSA|EC))$', re.I)

def length8(data, offset):
    value = data[offset]
    return (((value & 127) << 8) | data[offset + 1], offset + 2) if value & 128 else (value, offset + 1)


def length16(data, offset):
    value = struct.unpack_from('<H', data, offset)[0]
    return (((value & 32767) << 16) | struct.unpack_from('<H', data, offset + 2)[0], offset + 4) if value & 32768 else (value, offset + 2)


def encode8(value):
    if value >= 32768:
        raise ValueError('Manifest string too long')
    return bytes([128 | (value >> 8), value & 255]) if value >= 128 else bytes([value])


def patch_manifest(data):
    if struct.unpack_from('<HH', data) != (3, 8):
        raise ValueError('Not Android binary XML')
    chunks = []
    offset = 8
    strings = None
    pool_position = None
    pool_header = None
    while offset < len(data):
        kind, header, size = struct.unpack_from('<HHI', data, offset)
        chunk = bytearray(data[offset:offset + size])
        if len(chunk) != size or size < header or not size:
            raise ValueError('Invalid binary XML chunk')
        if kind == 1:
            pool_position = len(chunks)
            count, styles, flags, start, style_start = struct.unpack_from('<IIIII', chunk, 8)
            if styles:
                raise ValueError('Unexpected styled manifest string pool')
            pool_header = (header, flags)
            strings = []
            for i in range(count):
                p = start + struct.unpack_from('<I', chunk, header + i * 4)[0]
                if flags & 256:
                    _, p = length8(chunk, p)
                    length, p = length8(chunk, p)
                    strings.append(bytes(chunk[p:p + length]).decode('utf-8'))
                else:
                    length, p = length16(chunk, p)
                    strings.append(bytes(chunk[p:p + length * 2]).decode('utf-16le'))
        chunks.append((kind, header, chunk))
        offset += size
    if strings is None or pool_position is None:
        raise ValueError('Missing manifest string pool')
    old_strings = strings[:]
    strings = [NEW_PACKAGE + s[len(OLD_PACKAGE):] if s == OLD_PACKAGE or s.startswith(OLD_PACKAGE + '.') else s for s in strings]
    label_index = len(strings)
    strings.append(LABEL)
    version_index = len(strings)
    strings.append(VERSION)
    changes = []

    def value(chunk, attr):
        raw = struct.unpack_from('<I', chunk, attr + 8)[0]
        kind = chunk[attr + 15]
        number = struct.unpack_from('<I', chunk, attr + 16)[0]
        return old_strings[number] if kind == 3 else old_strings[raw] if raw != 0xffffffff else number

    def set_string(chunk, attr, index):
        struct.pack_into('<I', chunk, attr + 8, index)
        struct.pack_into('<HBBI', chunk, attr + 12, 8, 0, 3, index)

    for kind, header, chunk in chunks:
        if kind != 0x102:
            continue
        name = old_strings[struct.unpack_from('<I', chunk, header + 4)[0]]
        attr_start, attr_size, count = struct.unpack_from('<HHH', chunk, header + 8)
        if attr_size != 20:
            raise ValueError('Unexpected attribute size')
        attrs = {}
        for i in range(count):
            attr = header + attr_start + i * attr_size
            attr_name = old_strings[struct.unpack_from('<I', chunk, attr + 4)[0]]
            attrs[attr_name] = attr
        component = value(chunk, attrs['name']) if 'name' in attrs else None
        if name == 'manifest':
            if value(chunk, attrs['package']) != OLD_PACKAGE:
                raise ValueError('Unexpected source package')
            set_string(chunk, attrs['versionName'], version_index)
        if name in ('application', 'activity-alias') and 'label' in attrs:
            set_string(chunk, attrs['label'], label_index)
        if name == 'activity' and component == 'com.shilapi.xcertplay.CarPlayHostActivity':
            attr = attrs['screenOrientation']
            before = value(chunk, attr)
            if before != 10:
                raise ValueError('Expected fullSensor (10)')
            struct.pack_into('<I', chunk, attr + 8, 0xffffffff)
            struct.pack_into('<HBBI', chunk, attr + 12, 8, 0, 0x10, ORIENTATION)
            changes.append({'component': component, 'attribute': 'screenOrientation', 'before': 10, 'after': ORIENTATION})
    if len(changes) != 1:
        raise ValueError('Expected exactly one CarPlay orientation change')
    header, flags = pool_header
    offsets = []
    encoded = bytearray()
    for string in strings:
        offsets.append(len(encoded))
        utf16 = string.encode('utf-16le')
        units = len(utf16) // 2
        if flags & 256:
            utf8 = string.encode('utf-8')
            encoded += encode8(units) + encode8(len(utf8)) + utf8 + b'\0'
        else:
            if units >= 32768:
                raise ValueError('Unexpected long UTF-16 string')
            encoded += struct.pack('<H', units) + utf16 + b'\0\0'
    encoded += b'\0' * (-len(encoded) % 4)
    start = header + len(strings) * 4
    size = start + len(encoded)
    pool = bytearray(struct.pack('<HHIIIIII', 1, header, size, len(strings), 0, flags, start, 0))
    pool += b'\0' * (header - len(pool))
    pool += b''.join(struct.pack('<I', o) for o in offsets) + encoded
    chunks[pool_position] = (1, header, pool)
    body = b''.join(bytes(c) for _, _, c in chunks)
    manifest = struct.pack('<HHI', 3, 8, 8 + len(body)) + body
    return manifest, changes


def main():
    global SOURCE, OUT, PATHS, ORIENTATION
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=pathlib.Path, default=BASE / 'downloads/DiPlay-cn-v0.2.17-cn.2.apk')
    parser.add_argument('--output-dir', type=pathlib.Path, default=BASE / 'dist')
    parser.add_argument('--download', action='store_true', help='Download the exact official APK if input does not exist')
    parser.add_argument('--java-home', type=pathlib.Path, help='JDK directory containing bin/keytool and bin/jarsigner')
    parser.add_argument('--aapt2', default=os.environ.get('AAPT2', 'aapt2'), help='Android SDK aapt2 executable')
    parser.add_argument('--orientation', choices=['reverse-landscape', 'landscape'], default='reverse-landscape')
    args = parser.parse_args()
    SOURCE = args.input.resolve()
    OUT = args.output_dir.resolve()
    OUT.mkdir(parents=True, exist_ok=True)
    ORIENTATION = 8 if args.orientation == 'reverse-landscape' else 0
    java_home = args.java_home or (pathlib.Path(os.environ['JAVA_HOME']) if os.environ.get('JAVA_HOME') else None)
    def find_tool(name):
        candidate = str(java_home / 'bin' / name) if java_home else shutil.which(name)
        if not candidate or not pathlib.Path(candidate).is_file():
            parser.error('Missing JDK tool: ' + name)
        return candidate
    aapt = shutil.which(args.aapt2) or args.aapt2
    if not pathlib.Path(aapt).is_file():
        parser.error('Missing aapt2; pass --aapt2 with its SDK path')
    PATHS = {'keytool': find_tool('keytool'), 'jarsigner': find_tool('jarsigner'), 'aapt2': aapt}
    if not SOURCE.exists():
        if not args.download:
            parser.error('Official APK missing; use --download or --input')
        SOURCE.parent.mkdir(parents=True, exist_ok=True)
        temporary = SOURCE.with_suffix('.download')
        with urllib.request.urlopen(OFFICIAL_URL, timeout=60) as response, temporary.open('wb') as handle:
            shutil.copyfileobj(response, handle)
        temporary.replace(SOURCE)
    source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if source_hash != OFFICIAL_SHA256:
        raise ValueError('Input APK SHA-256 does not match the pinned official release')
    commands = []
    def run(arguments, env=None):
        result = subprocess.run(arguments, env=env, capture_output=True, text=True, timeout=120)
        commands.append({'tool': pathlib.Path(arguments[0]).name, 'exit_code': result.returncode})
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        return result.stdout
    with zipfile.ZipFile(SOURCE) as source:
        manifest, changes = patch_manifest(source.read('AndroidManifest.xml'))
        unsigned = OUT / 'unsigned.apk'
        with zipfile.ZipFile(unsigned, 'w') as target:
            for info in source.infolist():
                if SIGNATURE.match(info.filename):
                    continue
                content = manifest if info.filename == 'AndroidManifest.xml' else source.read(info.filename)
                target.writestr(copy.copy(info), content)
        (OUT / 'AndroidManifest.xml.bin').write_bytes(manifest)

    password_file = OUT / 'signing-password.txt'
    keystore = OUT / 'local-signing-key.p12'
    if password_file.exists():
        password = os.environ.get('DIPLAY_SIGNING_PASSWORD') or password_file.read_text().strip()
    else:
        password = os.environ.get('DIPLAY_SIGNING_PASSWORD') or secrets.token_urlsafe(32)
        descriptor = os.open(password_file, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, 'w') as handle:
            handle.write(password + '\n')
    sign_env = os.environ.copy()
    sign_env['DIPLAY_LOCAL_SIGNING_PASSWORD'] = password
    if not keystore.exists():
        run([PATHS['keytool'], '-genkeypair', '-keystore', str(keystore), '-storetype', 'PKCS12', '-alias', 'diplay-landscape', '-keyalg', 'RSA', '-keysize', '2048', '-validity', '3650', '-dname', 'CN=DiPlay Local Landscape Build', '-storepass:env', 'DIPLAY_LOCAL_SIGNING_PASSWORD', '-keypass:env', 'DIPLAY_LOCAL_SIGNING_PASSWORD'], env=sign_env)
        os.chmod(keystore, 0o600)
    signed = OUT / 'signed-unaligned.apk'
    run([PATHS['jarsigner'], '-keystore', str(keystore), '-storepass:env', 'DIPLAY_LOCAL_SIGNING_PASSWORD', '-keypass:env', 'DIPLAY_LOCAL_SIGNING_PASSWORD', '-sigalg', 'SHA256withRSA', '-digestalg', 'SHA-256', '-signedjar', str(signed), str(unsigned), 'diplay-landscape'], env=sign_env)

    apk = OUT / ('DiPlay-cn-v' + VERSION + '.apk')
    with zipfile.ZipFile(signed) as source, zipfile.ZipFile(apk, 'w') as target:
        for info in source.infolist():
            info = copy.copy(info)
            if info.compress_type == zipfile.ZIP_STORED:
                alignment = 4096 if info.filename.startswith('lib/') and info.filename.endswith('.so') else 4
                start = target.fp.tell() + 30 + len(info.filename.encode('utf-8')) + len(info.extra)
                padding = (-start) % alignment
                if padding:
                    if padding < 4:
                        padding += alignment
                    info.extra += struct.pack('<HH', 0xd935, padding - 4) + b'\0' * (padding - 4)
            target.writestr(info, source.read(info.filename))

    verification = run([PATHS['jarsigner'], '-J-Duser.language=en', '-J-Duser.country=US', '-verify', str(apk)])
    if 'jar verified' not in verification:
        raise ValueError('Signature verification did not confirm success')
    xmltree = run([PATHS['aapt2'], 'dump', 'xmltree', str(apk), '--file', 'AndroidManifest.xml'])
    (OUT / (VERSION + '-manifest-verified.txt')).write_text(xmltree)
    if NEW_PACKAGE not in xmltree or ('screenOrientation(0x0101001e)=' + str(ORIENTATION)) not in xmltree:
        raise ValueError('Compiled manifest verification failed')
    with zipfile.ZipFile(SOURCE) as original, zipfile.ZipFile(apk) as final:
        if final.testzip() is not None:
            raise ValueError('ZIP integrity verification failed')
        unchanged = []
        for info in original.infolist():
            if info.filename == 'AndroidManifest.xml' or SIGNATURE.match(info.filename):
                continue
            if original.read(info.filename) != final.read(info.filename):
                raise ValueError('Unexpected changed entry: ' + info.filename)
            unchanged.append(info.filename)
        native_alignment = []
        with apk.open('rb') as handle:
            for info in final.infolist():
                if info.filename.startswith('lib/') and info.filename.endswith('.so') and info.compress_type == 0:
                    handle.seek(info.header_offset)
                    header = handle.read(30)
                    name_len, extra_len = struct.unpack_from('<HH', header, 26)
                    offset = info.header_offset + 30 + name_len + extra_len
                    if offset % 4096:
                        raise ValueError('Unaligned native library')
                    native_alignment.append({'entry': info.filename, 'data_offset': offset})

    report = {
        'version': VERSION,
        'package': NEW_PACKAGE,
        'orientation_changes': changes,
        'input_sha256': source_hash,
        'apk_filename': apk.name,
        'apk_sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
        'bytes': apk.stat().st_size,
        'unchanged_non_signing_entries': len(unchanged),
        'signature_verified': True,
        'zip_integrity_verified': True,
        'native_page_alignment': native_alignment,
        'tools': commands,
        'scope': 'Manifest repack and signing verification only; no runtime stability claim.'
    }
    (OUT / 'build-verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
