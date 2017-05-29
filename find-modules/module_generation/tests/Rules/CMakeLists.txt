# Copyright 2017 Shaheed Haque <srhaque@theiet.org>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. The name of the author may not be used to endorse or promote products
#    derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS OR
# IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
# OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED.
# IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT
# NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF
# THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

#
# This is a helper script used to locate binaries, libraries and other
# platform-dependent items for use by the Python code. The output is
# NOT CMakeCache.txt et. al. but a JSON file:
#
#   {
#       "CXX_SOURCES": {
#           "KF5Activities": {
#               "LIBRARIES": "/usr/lib/x86_64-linux-gnu/libKF5Activities.so.5.31.0",
#               "INCLUDE_DIRS": "/usr/include/KF5/KActivities;/usr/include/KF5"
#           },
#           ...
#           "$": null
#       },
#       "CXX_DEPENDENCIES": {
#           "Qt5Widgets": {
#               "LIBRARIES": ...,
#               "INCLUDE_DIRS": ...,
#           },
#           "$": null
#       },
#       "CXX_COMPILE_OPTIONS": "-fPIC,-std=gnu++14",
#       "SIP_DEPENDENCIES": "/usr/share/sip/PyQt5",
#       "CXX_SOURCE_ROOT": "/usr/include/KF5",
#       "PY_PACKAGE": "PyKF5",
#       "$": null
#   }
#
# The "$" dict entries are a convenience which the caller discards.
#

cmake_minimum_required(VERSION 3.7)

project(PySample)

set(CXX_DEPENDENCIES Qt5Core)

#
# Find the list of targets for a Qt component.
#
function(get_qt5_targets component)
    string(REPLACE "Qt5" "Qt5::" target ${component})
    if(NOT TARGET ${target})
        message(STATUS "Ignoring invalid target \"${target}\" for ${component}")
        set(target "")
    endif()
    set(targets "${target}" PARENT_SCOPE)
endfunction(get_qt5_targets)

#
# Fetch a target property, recursing if necessary.
#
function(get_target_property_recursive target property)
    set(result)
    get_target_property(values ${target} ${property})
    if(values STREQUAL "values-NOTFOUND")
        # Skip
        message(STATUS "Warning: Target ${target} has no property ${property}")
    else()
        foreach(value ${values})
            string(FIND ${value} "$<TARGET_PROPERTY:" found)
            if(found EQUAL 0)
                #
                # Recurse. The format is:
                #
                # $<TARGET_PROPERTY:KF5::WebKit,INTERFACE_INCLUDE_DIRECTORIES>
                #
                string(REGEX REPLACE "\\$<TARGET_PROPERTY:(.*),(.*)>" "\\1" nested_tgt ${value})
                string(REGEX REPLACE "\\$<TARGET_PROPERTY:(.*),(.*)>" "\\2" nested_prop ${value})
                get_target_property_recursive(${nested_tgt} ${nested_prop})
                list(APPEND result ${get_target_property_recursive_result})
            else()
                list(APPEND result ${value})
            endif()
        endforeach()
    endif()
    set(get_target_property_recursive_result "${result}" PARENT_SCOPE)
endfunction(get_target_property_recursive)

#
# Find the includes, libraries etc. for a component.
#
function(get_targets_info dict component targets)
    if(targets STREQUAL "")
        message(STATUS "Warning: No targets for ${component}")
        return()
    endif()
    #
    # Make a combined list of includes, libraries etc.
    #
    set(libraries)
    set(includes)
    foreach(target ${targets})
        if(TARGET ${target})
            get_target_property(tmp ${target} LOCATION)
            list(APPEND libraries ${tmp})
            get_target_property_recursive(${target} INTERFACE_INCLUDE_DIRECTORIES)
            list(APPEND includes ${get_target_property_recursive_result})
        else()
            message(STATUS "Warning: Ignoring invalid target \"${target}\" in ${f}")
        endif()
    endforeach()
    #
    # De-duplicate and write results.
    #
    if(DEFINED includes)
        list(REMOVE_DUPLICATES includes)
        #
        # Not sure why the headers seem to include this.
        #
        list(REMOVE_ITEM includes "/usr/include")
    endif()
    file(APPEND "${dict}" "\"${component}\": {\n")
    file(APPEND "${dict}" "    \"LIBRARIES\": \"${libraries}\",\n")
    file(APPEND "${dict}" "    \"INCLUDE_DIRS\": \"${includes}\"\n")
    file(APPEND "${dict}" "},\n")
    set(includes "${includes}" PARENT_SCOPE)
endfunction(get_targets_info)

find_package(ECM REQUIRED NO_MODULE)
set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR} ${ECM_MODULE_PATH})
find_package(PyQt REQUIRED)
include(FeatureSummary)
#
# Write the values we found as a JSON blob.
#
set(dict ${CMAKE_CURRENT_BINARY_DIR}/configure.json)
message(STATUS "Writing ${dict}")
file(WRITE "${dict}" "{\n")
#
# Sources.
#
file(APPEND "${dict}" "\"CXX_SOURCES\": {\n")
foreach(component ${CXX_SOURCES})
endforeach()
set(CXX_SOURCE_ROOT)
#
# Write results.
#
file(APPEND "${dict}" "\"$\": null\n")
file(APPEND "${dict}" "},\n")
#
# Dependencies.
#
file(APPEND "${dict}" "\"CXX_DEPENDENCIES\": {\n")
foreach(component ${CXX_DEPENDENCIES})
    find_package(${component})
    get_qt5_targets(${component})
    get_targets_info(${dict} ${component} "${targets}")
endforeach()
file(APPEND "${dict}" "\"$\": null\n")
file(APPEND "${dict}" "},\n")
file(APPEND "${dict}" "\"CXX_COMPILE_OPTIONS\": \"-fPIC,-std=gnu++14\",\n")
file(APPEND "${dict}" "\"SIP_DEPENDENCIES\": \"${PyQt_INCLUDE_DIRS}\",\n")
file(APPEND "${dict}" "\"CXX_SOURCE_ROOT\": \"${CXX_SOURCE_ROOT}\",\n")
file(APPEND "${dict}" "\"SIP_PACKAGE\": \"${CMAKE_PROJECT_NAME}\",\n")
file(APPEND "${dict}" "\"$\": null\n")
file(APPEND "${dict}" "}\n")
unset(component)
unset(dict)
