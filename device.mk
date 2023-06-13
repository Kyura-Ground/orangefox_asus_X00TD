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
