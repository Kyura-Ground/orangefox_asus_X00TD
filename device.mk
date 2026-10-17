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
PRODUCT_USE_DYNAMIC_PARTITIONS := true
PRODUCT_RETROFIT_DYNAMIC_PARTITIONS := true

PRODUCT_PACKAGES += fastbootd

PRODUCT_PACKAGES += qcom_decrypt qcom_decrypt_fbe

# Match the current Android 17 ROM rather than the old tree's future dates.
PLATFORM_VERSION := 17.0.0
PLATFORM_VERSION_LAST_STABLE := $(PLATFORM_VERSION)
PLATFORM_SECURITY_PATCH := 2026-10-01
VENDOR_SECURITY_PATCH := 2025-01-05

PRODUCT_SYSTEM_DEFAULT_PROPERTIES += \
    keymaster_ver=3.0
