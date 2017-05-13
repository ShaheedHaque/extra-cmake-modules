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

cmake_minimum_required(VERSION 3.4)

project(sip_module_generation)

include(FindSIP.cmake)
include(FindClang.cmake)
include(FindLibClang.cmake)

enable_testing()

if(SIP_VERSION VERSION_LESS 4.19)
    message(SEND_ERROR "SIP version \"${SIP_VERSION}\" too old")
elif(Clang_VERSION VERSION_LESS 3.9)
    message(SEND_ERROR "Clang version \"${Clang_VERSION}\" too old")
elif(LibClang_VERSION VERSION_LESS 3.9)
    message(SEND_ERROR "LibClang version \"${LibClang_VERSION}\" too old")
else()
    #
    # Write the values we found.
    #
    file(WRITE "${CMAKE_CURRENT_SOURCE_DIR}/configure.py"
"
SIP_EXECUTABLE = \"${SIP_EXECUTABLE}\"
CLANG_EXECUTABLE = \"${Clang_EXECUTABLE}\"
LIBCLANG_LIBRARY = \"${LibClang_LIBRARY}\"
")
endif()
