#!/usr/bin/env bash
# Source this before lunch; OrangeFox variables are shell exports.
export FOX_BUILD_DEVICE=X00TD
export FOX_TARGET_DEVICES="X00TD,X00T,ASUS_X00TD"
export OF_MAINTAINER=ikwfahmi
export FOX_VARIANT=FBEv1_4.4
export FOX_VANILLA_BUILD=1
export OF_DEFAULT_KEYMASTER_VERSION=3.0
# Keep data/media available during FBE initialization.
export OF_FIX_DECRYPTION_ON_DATA_MEDIA=1
export OF_SCREEN_H=2160
export OF_ALLOW_DISABLE_NAVBAR=0
export OF_DEFAULT_TIMEZONE="WIB-7"
# Preserve the ROM's encryption and boot image during ZIP installation.
export OF_DONT_PATCH_ENCRYPTED_DEVICE=1
export OF_SKIP_ORANGEFOX_PROCESS=1
export OF_DISABLE_MIUI_SPECIFIC_FEATURES=1
