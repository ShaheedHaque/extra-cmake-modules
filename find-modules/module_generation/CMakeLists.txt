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
# platform- and system-dependent items for use by the Python code.
#
cmake_minimum_required(VERSION 3.4)

project(sip_module_generation)

set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR})
find_package(SIP REQUIRED)
find_package(Clang)
find_package(LibClang REQUIRED)

if(NOT ClangPP_FOUND)
    message(SEND_ERROR "Clang++ not found")
elif(SIP_VERSION VERSION_LESS 4.19)
    message(SEND_ERROR "SIP version \"${SIP_VERSION}\" too old")
elif(ClangPP_VERSION VERSION_LESS 3.9)
    message(SEND_ERROR "Clang++ version \"${ClangPP_VERSION}\" too old")
elif(LibClang_VERSION VERSION_LESS 3.9)
    message(SEND_ERROR "LibClang version \"${LibClang_VERSION}\" too old")
else()
    #
    # Write the values we found as a JSON blob.
    #
    set(dict "${CMAKE_CURRENT_BINARY_DIR}/configure.json")
    file(WRITE "${dict}" "{")
    file(APPEND "${dict}" "\"SIP_EXECUTABLE\": \"${SIP_EXECUTABLE}\",")
    file(APPEND "${dict}" "\"CLANGPP_EXECUTABLE\": \"${ClangPP_EXECUTABLE}\",")
    file(APPEND "${dict}" "\"LIBCLANG_LIBRARY\": \"${LibClang_LIBRARY}\",")
    file(APPEND "${dict}" "\"terminator\": null")
    file(APPEND "${dict}" "}")
endif()
