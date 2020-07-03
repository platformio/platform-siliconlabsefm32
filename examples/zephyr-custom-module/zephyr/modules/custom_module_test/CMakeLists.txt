# Makefile - STLIB SDK
#
# Copyright (c) 2016 Linaro Limited
#
# SPDX-License-Identifier: Apache-2.0

zephyr_library()

zephyr_library_sources("src/custom_module_test.c")
zephyr_include_directories("inc")
