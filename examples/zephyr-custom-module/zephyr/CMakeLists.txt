# SPDX-License-Identifier: Apache-2.0

set(
    ZEPHYR_EXTRA_MODULES
    "${CMAKE_CURRENT_SOURCE_DIR}/modules/custom_module"
    "${CMAKE_CURRENT_SOURCE_DIR}/modules/custom_module_test"
)

cmake_minimum_required(VERSION 3.13.1)
include($ENV{ZEPHYR_BASE}/cmake/app/boilerplate.cmake NO_POLICY_SCOPE)
project(custom-module)

target_sources(app PRIVATE ../src/main.c)
