cmake_minimum_required(VERSION 2.8.12)

project(old_version_file)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR}/../../../modules)
include(ECMSetupVersion)

ecm_setup_version(2.3.4
    VARIABLE_PREFIX Foo
    PACKAGE_VERSION_FILE FooVersion.cmake
)

include(../version_helpers.cmake)

standard_version_var_checks(Foo 2.3.4)
AnyNewer_2_3_4_checks("${CMAKE_CURRENT_BINARY_DIR}/FooVersion.cmake")

add_executable(dummy main.c)
