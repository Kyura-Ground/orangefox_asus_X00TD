#!/usr/bin/env python3
"""Check the packaged X00TD recovery before a device boot test."""
import gzip
import json
from pathlib import Path
import re
import struct
import sys
import zlib


def cpio_entries(archive):
    offset = 0
    result = {}
    while archive[offset:offset + 6] == b"070701":
        fields = [int(archive[offset + 6 + i * 8:offset + 14 + i * 8], 16)
                  for i in range(13)]
        name = archive[offset + 110:offset + 109 + fields[11]].decode()
        if name.startswith('./'):
            name = name[2:]
        start = (offset + 110 + fields[11] + 3) & ~3
        end = start + fields[6]
        if name == 'TRAILER!!!':
            return result
        assert end <= len(archive), 'Truncated recovery ramdisk'
        result[name] = archive[start:end]
        offset = (end + 3) & ~3
    raise ValueError('Invalid or unterminated recovery ramdisk')


def check_image(path):
    image = path.read_bytes()
    assert 0 < len(image) <= 67108864, 'Recovery exceeds the 64 MiB partition'
    assert image[:8] == b'ANDROID!', 'Wrong boot image magic'
    assert struct.unpack_from('<I', image, 40)[0] == 1, 'Boot header must be v1'
    page = struct.unpack_from('<I', image, 36)[0]
    assert page == 4096, 'Wrong boot image page size'
    kernel_size = struct.unpack_from('<I', image, 8)[0]
    ramdisk_size = struct.unpack_from('<I', image, 16)[0]
    ramdisk_offset = page + ((kernel_size + page - 1) // page) * page
    assert ramdisk_offset + ramdisk_size <= len(image), 'Truncated boot image'
    cmdline = image[64:576].split(b'\0')[0] + b' ' + image[608:1632].split(b'\0')[0]
    assert b'androidboot.super_partition=system' in cmdline, 'Wrong retrofit metadata device'
    assert b'androidboot.dynamic_partitions_retrofit=true' in cmdline, 'Missing retrofit flag'
    kernel = image[page:page + kernel_size]
    raw_kernel = zlib.decompress(kernel, 31)
    version = re.search(rb'Linux version 4\.19\.[^\x00\n]+', raw_kernel)
    assert version, 'The image must contain the device 4.19 kernel'
    first = raw_kernel.find(b'IKCFG_ST')
    last = raw_kernel.find(b'IKCFG_ED', first)
    assert first >= 0 and last > first, 'Kernel configuration is missing'
    config = gzip.decompress(raw_kernel[first + 8:last]).decode()
    required = ['CONFIG_ION=y', 'CONFIG_FS_ENCRYPTION=y', 'CONFIG_FS_VERITY=y',
                'CONFIG_EXT4_FS=y', 'CONFIG_F2FS_FS=y', 'CONFIG_DM_CRYPT=y',
                'CONFIG_SECURITY_SELINUX_DEVELOP=y', 'CONFIG_PSTORE_PMSG=y',
                'CONFIG_VSOCKETS=y']
    for option in required:
        assert option in config.splitlines(), f'Missing kernel capability: {option}'
    assert '# CONFIG_DMABUF_SYSFS_STATS is not set' in config, 'Unsafe legacy ION stats configuration'
    ramdisk = image[ramdisk_offset:ramdisk_offset + ramdisk_size]
    files = cpio_entries(gzip.decompress(ramdisk))
    required_files = [
        'system/bin/recovery', 'system/bin/fastbootd', 'system/bin/prepdecrypt.sh',
        'system/bin/qseecomd',
        'system/bin/android.hardware.keymaster@3.0-service-qti',
        'system/bin/android.hardware.gatekeeper@1.0-service-qti',
        'init.recovery.qcom_decrypt.rc', 'init.recovery.qcom_decrypt.fbe.rc',
        'vendor/lib64/hw/android.hardware.keymaster@3.0-impl-qti.so',
        'vendor/lib64/hw/android.hardware.gatekeeper@1.0-impl-qti.so',
    ]
    for name in required_files:
        assert name in files, f'Missing packaged dependency: {name}'
    fstab = files['system/etc/recovery.fstab'].decode()
    entries = [line.split() for line in fstab.splitlines()
               if line.strip() and not line.lstrip().startswith('#')]
    for name in ['system', 'system_ext', 'product', 'vendor', 'odm']:
        assert any(row[0] == name and 'logical' in row[4].split(',')
                   for row in entries), f'{name} must be a logical partition'
    data = [row for row in entries if row[1] == '/data']
    assert {row[2] for row in data} == {'ext4', 'f2fs'}, 'Missing userdata filesystem'
    for row in data:
        assert 'fileencryption=aes-256-xts:aes-256-cts:v2+emmc_optimized' in row[4].split(',')
        assert 'metadata_encryption=' not in row[4], 'ROM does not use metadata encryption'
    return {'image': str(path), 'bytes': len(image), 'kernel': version[0].decode(),
            'header_version': 1, 'logical_partitions': 5, 'FBE_policy': 'v2+emmc_optimized',
            'packaging_checks': 'passed', 'device_boot_and_decryption_test': 'still required'}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.exit('Usage: check-recovery.py path/to/recovery.img')
    try:
        print(json.dumps(check_image(Path(sys.argv[1])), indent=2))
    except (AssertionError, KeyError, ValueError, OSError, EOFError, struct.error, zlib.error) as error:
        sys.exit(f'Recovery image check failed: {error}')
