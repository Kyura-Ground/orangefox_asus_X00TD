#!/usr/bin/env bash
# Run from the root of a synced OrangeFox 12.1 source checkout.
set -eo pipefail

device_path=device/asus/X00TD
if [[ ! -f build/envsetup.sh || ! -f bootable/recovery/orangefox.mk || ! -d vendor/recovery ]]; then
    echo 'Run this script from the OrangeFox source root.' >&2
    exit 1
fi
for dependency in device/qcom/common device/qcom/twrp-common; do
    [[ -d "$dependency" ]] || { echo "Missing dependency: $dependency" >&2; exit 1; }
done

source "$device_path/orangefox-config.sh"
source build/envsetup.sh
lunch twrp_X00TD-eng
[[ $(get_build_var PLATFORM_SDK_VERSION) == 32 ]] || {
    echo 'This tree requires the OrangeFox 12.1 build base (SDK 32).' >&2
    exit 1
}

if [[ ${X00TD_BUILD_KERNEL_FROM_SOURCE:-false} != true ]]; then
    (cd "$device_path/prebuilt" && sha256sum -c kernel.sha256)
    python3 "$device_path/tools/check-recovery.py" --kernel "$device_path/prebuilt/Image.gz-dtb"
fi

patch_path="$PWD/$device_path/patches/retrofit-super-image.patch"
if git -C bootable/recovery apply --reverse --check "$patch_path" 2>/dev/null; then
    echo 'Retrofit super image patch is already applied.'
else
    git -C bootable/recovery apply --check "$patch_path"
    git -C bootable/recovery apply "$patch_path"
fi

m -j"${BUILD_JOBS:-$(nproc)}" recoveryimage
python3 "$device_path/tools/check-recovery.py" "${ANDROID_PRODUCT_OUT:-${OUT_DIR:-out}/target/product/X00TD}/recovery.img"
