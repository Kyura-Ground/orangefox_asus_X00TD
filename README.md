# OrangeFox for ASUS ZenFone Max Pro M1

Branch `fox_12.1-4.4` targets the X00TD LineageOS 23.2 / Android 16 tree
with kernel 4.4, physical system/vendor partitions, and FBEv1 Qualcomm ICE.
Build it with the OrangeFox **12.1 source base**, independently of the
Android version installed on the phone.

The existing `OrangeFox` branch is the separate 4.19 / dynamic-partition
configuration. Its recovery images are not interchangeable with this tree.

## Build

Sync a separate OrangeFox checkout using the official sync script:

```sh
git clone https://gitlab.com/OrangeFox/sync.git OrangeFox_sync
cd OrangeFox_sync
./orangefox_sync.sh --branch 12.1 --path ~/fox_12.1
cd ~/fox_12.1
git clone --branch fox_12.1-4.4 \
    https://github.com/Kyura-Ground/orangefox_asus_X00TD.git device/asus/X00TD
BUILD_JOBS=192 bash device/asus/X00TD/script.sh
```

The sync script supplies `device/qcom/common` and `device/qcom/twrp-common`.
The device build script loads the OrangeFox exports, applies the retained
GUI lifetime and crash-dumper patches, and checks the packaged recovery.
Output is in `out/target/product/X00TD/`.

The default prebuilt kernel is the unmodified `Image.gz-dtb` from
[CircleCI pipeline 377](https://app.circleci.com/pipelines/gh/Kyura-Ground/cooking-kernel/377).
Its exact source revision and SHA-256 are recorded in `prebuilt/`.
No AnyKernel installation or boot-image patch is involved.

To compile the kernel inline instead:

```sh
git clone --branch lineage-23.2 \
    https://github.com/Kyura-Ground/android_kernel_asus_sdm660.git kernel/asus/sdm660
X00TD_BUILD_KERNEL_FROM_SOURCE=true BUILD_JOBS=192 bash device/asus/X00TD/script.sh
```

## Layout and encryption

- Boot header v0, 4096-byte pages, appended DTB, dedicated 64 MiB recovery.
- Physical `system` and `vendor`; no retrofit super or fastbootd.
- Ext4 userdata with `fileencryption=ice`, matching the ROM fstab.
- `/metadata` is a temporary tmpfs, matching the ROM. `logdump` is untouched.
- Qualcomm Keymaster 3.0 / Gatekeeper 1.0 binaries come from the 4.4 vendor
  tree; `proprietary-files.txt` records their origin and hashes.
- Decryption preparation reads the installed ROM's version and patch levels.
- `TW_USE_FSCRYPT_POLICY=2` selects the current TWRP policy-union API; it does
  not select an FBEv2 userdata policy. The fstab still requests FBEv1 ICE.
- OrangeFox ROM encryption/verity patching is disabled.

Full recovery compilation and device tests remain required. Test recovery
startup, touch/brightness, ADB/sideload/MTP, PIN-protected userdata decryption,
and installation of the matching A16 ROM before treating the build as ready.

References: [OrangeFox X00T](https://gitlab.com/OrangeFox/device/x00t),
[TeamWin X00T](https://github.com/TeamWin/android_device_asus_X00T),
[OrangeFox build guide](https://wiki.orangefox.tech/en/dev/building).
