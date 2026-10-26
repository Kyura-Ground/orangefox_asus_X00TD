#
# Copyright (C) 2023 The Android Open Source Project
# Copyright (C) 2023 SebaUbuntu's TWRP device tree generator
# Copyright (C) 2026 ikwfahmi
# SPDX-License-Identifier: Apache-2.0
#

DEVICE_PATH := device/asus/X00TD
$(call inherit-product, $(SRC_TARGET_DIR)/product/aosp_base.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)

PRODUCT_SHIPPING_API_LEVEL := 27
PRODUCT_SOONG_NAMESPACES += $(DEVICE_PATH)

PRODUCT_PACKAGES += qcom_decrypt qcom_decrypt_fbe

# Keymaster OS version matches the Android 16 ROM.
PLATFORM_VERSION := 16.0.0
PLATFORM_VERSION_LAST_STABLE := $(PLATFORM_VERSION)
PLATFORM_SECURITY_PATCH := 2026-10-01
VENDOR_SECURITY_PATCH := 2020-12-05

PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    keymaster_ver=3.0 \
    ro.crypto.volume.filenames_mode=aes-256-cts
