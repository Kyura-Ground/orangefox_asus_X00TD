#!/usr/bin/env python3
"""Check the packaged X00TD recovery before a device boot test."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import zlib
import xml.etree.ElementTree as ET


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


def check_kernel(kernel):
    inflater = zlib.decompressobj(31)
    raw_kernel = inflater.decompress(kernel)
    assert inflater.eof, 'Truncated compressed kernel'
    version = re.search(rb'Linux version 4\.4\.[^\x00\n]+', raw_kernel)
    assert version, 'The image must contain the device 4.4 kernel'
    first = raw_kernel.find(b'IKCFG_ST')
    last = raw_kernel.find(b'IKCFG_ED', first)
    assert first >= 0 and last > first, 'Kernel configuration is missing'
    config = gzip.decompress(raw_kernel[first + 8:last]).decode()
    required = ['CONFIG_ION=y', 'CONFIG_EXT4_ENCRYPTION=y',
                'CONFIG_EXT4_FS_ENCRYPTION=y', 'CONFIG_EXT4_FS_ICE_ENCRYPTION=y',
                'CONFIG_CRYPTO_DEV_QCOM_ICE=y', 'CONFIG_USB_CONFIGFS_F_FS=y',
                'CONFIG_USB_CONFIGFS_F_MTP=y',
                'CONFIG_EXT4_FS=y', 'CONFIG_F2FS_FS=y', 'CONFIG_DM_CRYPT=y',
                'CONFIG_SECURITY_SELINUX_DEVELOP=y']
    for option in required:
        assert option in config.splitlines(), f'Missing kernel capability: {option}'
    dtbs = inflater.unused_data
    offset = 0
    dtb_count = 0
    while offset < len(dtbs):
        assert dtbs[offset:offset + 4] == b'\xd0\x0d\xfe\xed', 'Missing or invalid appended DTB'
        size = struct.unpack_from('>I', dtbs, offset + 4)[0]
        assert 40 <= size <= len(dtbs) - offset, 'Truncated appended DTB'
        offset += size
        dtb_count += 1
    assert dtb_count > 0, 'This device needs an appended DTB'
    return {'version': version[0].decode(), 'sha256': hashlib.sha256(kernel).hexdigest(),
            'appended_dtbs': dtb_count, 'FBE_policy': 'v1 (Qualcomm ICE)',
            'vsockets': 'CONFIG_VSOCKETS=y' in config.splitlines()}


def check_image(path):
    image = path.read_bytes()
    assert 0 < len(image) <= 67108864, 'Recovery exceeds the 64 MiB partition'
    assert image[:8] == b'ANDROID!', 'Wrong boot image magic'
    assert struct.unpack_from('<I', image, 40)[0] == 0, 'Boot header must be v0'
    page = struct.unpack_from('<I', image, 36)[0]
    assert page == 4096, 'Wrong boot image page size'
    kernel_size = struct.unpack_from('<I', image, 8)[0]
    ramdisk_size = struct.unpack_from('<I', image, 16)[0]
    ramdisk_offset = page + ((kernel_size + page - 1) // page) * page
    assert ramdisk_offset + ramdisk_size <= len(image), 'Truncated boot image'
    cmdline = image[64:576].split(b'\0')[0] + b' ' + image[608:1632].split(b'\0')[0]
    assert b'androidboot.super_partition=' not in cmdline, 'Unexpected super partition'
    assert b'androidboot.dynamic_partitions' not in cmdline, 'Unexpected dynamic partitions'
    for arg in [b'androidboot.configfs=true', b'androidboot.usbcontroller=a800000.dwc3',
                b'androidboot.android_dt_dir=/non-existent',
                b'androidboot.boot_devices=soc/c0c4000.sdhci']:
        assert arg in cmdline.split(), f'Missing recovery boot argument: {arg.decode()}'
    kernel = image[page:page + kernel_size]
    kernel_info = check_kernel(kernel)
    ramdisk = image[ramdisk_offset:ramdisk_offset + ramdisk_size]
    files = cpio_entries(gzip.decompress(ramdisk))
    required_files = [
        'system/bin/recovery', 'system/bin/prepdecrypt.sh',
        'system/bin/hwservicemanager', 'system/bin/crash_dump64',
        'system/etc/vintf/manifest.xml',
        'system/etc/task_profiles.json',
        'system/bin/qseecomd',
        'system/lib64/libion.so', 'system/lib64/libxml2.so',
        'system/lib64/libhidltransport.so', 'system/lib64/libhwbinder.so',
        'system/lib64/libhardware_legacy.so',
        'system/bin/android.hardware.keymaster@3.0-service-qti',
        'system/bin/android.hardware.gatekeeper@1.0-service-qti',
        'init.recovery.qcom_decrypt.rc', 'init.recovery.qcom_decrypt.fbe.rc',
        'vendor/lib64/hw/android.hardware.keymaster@3.0-impl-qti.so',
        'vendor/lib64/hw/android.hardware.gatekeeper@1.0-impl-qti.so',
    ]
    for name in required_files:
        assert name in files, f'Missing packaged dependency: {name}'
    assert b'Apex is disabled in this build' in files['system/bin/recovery'], \
        'Recovery must be rebuilt with TW_EXCLUDE_APEX=true'
    framework = ET.fromstring(files['system/etc/vintf/manifest.xml'])
    assert framework.get('type') == 'framework', 'Wrong framework manifest type'
    services = {(hal.findtext('name'), hal.findtext('transport'), hal.findtext('fqname'))
                for hal in framework.findall('hal')}
    assert ('android.hidl.manager', 'hwbinder', '@1.2::IServiceManager/default') in services, \
        'Missing framework HIDL service manager declaration'
    assert ('android.hidl.token', 'hwbinder', '@1.0::ITokenManager/default') in services, \
        'Missing framework HIDL token manager declaration'
    profiles = json.loads(files['system/etc/task_profiles.json'])
    names = {profile['Name'] for section in ['Profiles', 'AggregateProfiles']
             for profile in profiles[section]}
    assert {'SCHED_SP_DEFAULT', 'SCHED_SP_BACKGROUND', 'CPUSET_SP_DEFAULT',
            'CPUSET_SP_SYSTEM'} <= names, 'Missing standard process profiles'
    for aggregate in profiles['AggregateProfiles']:
        assert set(aggregate['Profiles']) <= names, 'Unresolved aggregate task profile'
    fstab = files['system/etc/recovery.fstab'].decode()
    entries = [line.split() for line in fstab.splitlines()
               if line.strip() and not line.lstrip().startswith('#')]
    for name, mountpoint in [('system', '/system_root'), ('vendor', '/vendor')]:
        assert any(row[0] == '/dev/block/bootdevice/by-name/' + name and
                   row[1] == mountpoint and row[2] == 'ext4' for row in entries), \
            f'{name} must use the physical partition'
    assert all('logical' not in row[4].split(',') for row in entries), \
        'Unexpected logical partition'
    assert not any(row[1] == '/metadata' for row in entries), \
        'This ROM uses temporary metadata, not a block device'
    assert b'mount tmpfs tmpfs /metadata size=10m' in files['init.recovery.qcom.rc'], \
        'Missing temporary metadata mount'
    flags = files['system/etc/twrp.flags'].decode()
    assert '/metadata ' not in flags and 'logdump' not in flags, \
        'Unexpected physical metadata override'
    data = [row for row in entries if row[1] == '/data']
    assert len(data) == 1 and data[0][2] == 'ext4', 'ROM userdata must be ext4'
    assert 'fileencryption=ice' in data[0][4].split(','), 'Wrong FBE policy'
    assert 'metadata_encryption=' not in data[0][4], 'ROM does not use metadata encryption'
    assert b'/sys/class/leds/lcd-backlight/brightness 128' in files['init.recovery.usb.rc'], \
        'Wrong kernel 4.4 backlight path'
    return {'image': str(path), 'bytes': len(image), 'kernel': kernel_info,
            'header_version': 0, 'physical_partitions': ['system', 'vendor'],
            'FBE_policy': 'v1 (Qualcomm ICE)',
            'framework_hidl_managers': 2, 'task_profiles': len(profiles['Profiles']),
            'metadata': 'tmpfs', 'native_crash_helper': True,
            'apex_loading': False,
            'packaging_checks': 'passed', 'device_boot_and_decryption_test': 'still required'}


if __name__ == '__main__':
    try:
        if len(sys.argv) == 3 and sys.argv[1] == '--kernel':
            result = check_kernel(Path(sys.argv[2]).read_bytes())
        elif len(sys.argv) == 2:
            result = check_image(Path(sys.argv[1]))
        else:
            sys.exit('Usage: check-recovery.py [--kernel] path/to/image')
        print(json.dumps(result, indent=2))
    except (AssertionError, KeyError, ValueError, OSError, EOFError, struct.error, zlib.error,
            ET.ParseError) as error:
        sys.exit(f'Recovery image check failed: {error}')
