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

#.rst:
# FindClang
# ---------
#
# Find Clang
#
# This module finds an installed Clang.  It sets the following variables:
#
# ::
#
#   Clang_FOUND - set to true if clang is found
#   Clang_DIR - the directory where clang is installed
#   Clang_EXECUTABLE - the path to the clang executable
#   Clang_VERSION - Version number of the clang executable as a string (e.g. "3.9")
#   ClangPP_FOUND - set to true if clang++ is found
#   ClangPP_DIR - the directory where clang++ is installed
#   ClangPP_EXECUTABLE - the path to the clang++ executable
#   ClangPP_VERSION - Version number of the clang++ executable as a string (e.g. "3.9")
#
# The minimum required version of Clang can be specified using the
# standard syntax, e.g.  find_package(Clang 4.19)
#
# All information is collected from the Clang/PP_EXECUTABLE so the version
# to be found can be changed from the command line by means of setting
# Clang/PP_EXECUTABLE

find_program(Clang_EXECUTABLE NAMES clang-4.0 clang-3.9)

if(Clang_EXECUTABLE)
  execute_process(COMMAND ${Clang_EXECUTABLE} -v
    OUTPUT_VARIABLE Clang_version_output
    ERROR_VARIABLE Clang_version_output
    RESULT_VARIABLE Clang_version_result)

  if(Clang_version_result)
    message(SEND_ERROR "Command \"${Clang_EXECUTABLE} -v\" failed with output:\n${Clang_version_output}")
  else()
    string(REGEX REPLACE "clang version[ ]+\([0-9]+.[0-9]+.[^ ]+\)[ ]+.*" "\\1" Clang_version_output ${Clang_version_output})
    set(Clang_VERSION ${Clang_version_output} CACHE STRING "Clang version" FORCE)
  endif()
endif()

include(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(Clang REQUIRED_VARS Clang_EXECUTABLE
                                        VERSION_VAR Clang_VERSION)


find_program(ClangPP_EXECUTABLE NAMES clang++-4.0 clang++-3.9)

if(ClangPP_EXECUTABLE)
  execute_process(COMMAND ${ClangPP_EXECUTABLE} -v
    OUTPUT_VARIABLE ClangPP_version_output
    ERROR_VARIABLE ClangPP_version_output
    RESULT_VARIABLE ClangPP_version_result)

  if(ClangPP_version_result)
    message(SEND_ERROR "Command \"${ClangPP_EXECUTABLE} -v\" failed with output:\n${ClangPP_version_output}")
  else()
    string(REGEX REPLACE "clang version[ ]+\([0-9]+.[0-9]+.[^ ]+\)[ ]+.*" "\\1" ClangPP_version_output ${ClangPP_version_output})
    set(ClangPP_VERSION ${ClangPP_version_output} CACHE STRING "ClangPP version" FORCE)
  endif()
endif()

include(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(ClangPP REQUIRED_VARS ClangPP_EXECUTABLE
                                          VERSION_VAR ClangPP_VERSION)

mark_as_advanced(Clang_VERSION ClangPP_VERSION)
