#!/usr/bin/env bash
# Source this before lunch; OrangeFox variables are shell exports.
export FOX_BUILD_DEVICE=X00TD
export FOX_TARGET_DEVICES="X00TD,X00T,ASUS_X00TD"
export OF_MAINTAINER=ikwfahmi
export FOX_VARIANT=FBEv2_4.19
export FOX_VANILLA_BUILD=1
export OF_DEFAULT_KEYMASTER_VERSION=3.0
# Prepare data/media before installing filesystem-scoped FBEv2 keys.
export OF_FIX_DECRYPTION_ON_DATA_MEDIA=1
export OF_SCREEN_H=2160
export OF_ALLOW_DISABLE_NAVBAR=0
export OF_DEFAULT_TIMEZONE="WIB-7"
