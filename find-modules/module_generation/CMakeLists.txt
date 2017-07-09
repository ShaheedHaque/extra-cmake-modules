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
#       "SIP_EXECUTABLE": "/usr/bin/sip",
#       "ClangPP_EXECUTABLE": "/usr/bin/clang++-3.9",
#       "ClangPP_SYS_INCLUDES": "/usr/bin/...;/usr/bin/...",
#       "LibClang_LIBRARY": "/usr/lib/x86_64-linux-gnu/libclang-3.9.so",
#       "$": null
#   }
#
# The "$" dict entries are a convenience which the caller discards.
#

cmake_minimum_required(VERSION 3.7)

project(sip_module_generation)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR})
find_package(SIP REQUIRED)
find_package(Clang REQUIRED)
find_package(LibClang REQUIRED)

if(NOT ClangPP_FOUND)
    message(SEND_ERROR "Clang++ not found")
elseif(SIP_VERSION VERSION_LESS 4.19.3)
    message(SEND_ERROR "SIP version \"${SIP_VERSION}\" too old")
elseif(ClangPP_VERSION VERSION_LESS 3.9)
    message(SEND_ERROR "Clang++ version \"${ClangPP_VERSION}\" too old")
elseif(LibClang_VERSION VERSION_LESS 3.9)
    message(SEND_ERROR "LibClang version \"${LibClang_VERSION}\" too old")
else()
    #
    # Find the system includes used by clang++. This is modelled on a part of Steve Kelley's
    # FindPythonModuleGeneration.cmake.
    #
    execute_process(COMMAND ${ClangPP_EXECUTABLE} -v -E -x c++ -
                    ERROR_VARIABLE _compilerOutput
                    OUTPUT_VARIABLE _compilerStdout
                    INPUT_FILE /dev/null)
    if("${_compilerOutput}" MATCHES "> search starts here[^\n]+\n *(.+ *\n) *End of (search) list")
        # split the output into lines and then remove leading and trailing spaces from each of them:
        string(REGEX MATCHALL "[^\n]+\n" _includeLines "${CMAKE_MATCH_1}")
        foreach(nextLine ${_includeLines})
            # on OSX, gcc says things like this:  "/System/Library/Frameworks (framework directory)", strip the last part
            string(REGEX REPLACE "\\(framework directory\\)" "" nextLineNoFramework "${nextLine}")
            # strip spaces at the beginning and the end
            string(STRIP "${nextLineNoFramework}" _includePath)
            list(APPEND ClangPP_SYS_INCLUDES "${_includePath}")
        endforeach()
    endif()
    #
    # Write the values we found as a JSON blob.
    #
    set(dict ${CMAKE_CURRENT_BINARY_DIR}/configure.json)
    message(STATUS "Writing ${dict}")
    file(WRITE "${dict}" "{\n")
    foreach(var "SIP_EXECUTABLE" "ClangPP_EXECUTABLE" "ClangPP_SYS_INCLUDES" "LibClang_LIBRARY")
        file(APPEND "${dict}" "\"${var}\": \"${${var}}\",\n")
    endforeach()
    file(APPEND "${dict}" "\"$\": null\n")
    file(APPEND "${dict}" "}\n")
endif()
