#
# Copyright (C) 2023 The Android Open Source Project
# Copyright (C) 2023 SebaUbuntu's TWRP device tree generator
# Copyright (C) 2026 ikwfahmi
# SPDX-License-Identifier: Apache-2.0
#

$(call inherit-product, vendor/twrp/config/common.mk)
$(call inherit-product, device/asus/X00TD/device.mk)

PRODUCT_DEVICE := X00TD
PRODUCT_NAME := twrp_X00TD
PRODUCT_BRAND := asus
PRODUCT_MODEL := ASUS Zenfone Max Pro M1
PRODUCT_MANUFACTURER := asus
PRODUCT_RELEASE_NAME := X00TD
