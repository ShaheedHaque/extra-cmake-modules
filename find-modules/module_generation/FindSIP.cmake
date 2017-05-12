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
# FindSIP
# -------
#
# Find SIP
#
# This module finds an installed SIP.  It sets the following variables:
#
# ::
#
#   SIP_FOUND - set to true if SIP is found
#   SIP_DIR - the directory where SIP is installed
#   SIP_EXECUTABLE - the path to the SIP executable
#   SIP_VERSION - the version number of the SIP executable
#
#
#
# The minimum required version of SIP can be specified using the
# standard syntax, e.g.  find_package(SIP 4.19)
#
# All information is collected from the SIP_EXECUTABLE so the version
# to be found can be changed from the command line by means of setting
# SIP_EXECUTABLE

find_program(SIP_EXECUTABLE NAMES sip)

if(SIP_EXECUTABLE)
  execute_process(COMMAND ${SIP_EXECUTABLE} -V
    OUTPUT_VARIABLE SIP_version_output
    ERROR_VARIABLE SIP_version_output
    RESULT_VARIABLE SIP_version_result)

  if(SIP_version_result)
    message(SEND_ERROR "Command \"${SIP_EXECUTABLE} -V\" failed with output:\n${SIP_version_output}")
  else()
    string(REGEX REPLACE "[\n\r]+" "" SIP_version_output ${SIP_version_output})
    set(SIP_VERSION ${SIP_version_output} CACHE STRING "SIP version" FORCE)
  endif()
endif()

include(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(SIP REQUIRED_VARS SIP_EXECUTABLE
                                      VERSION_VAR SIP_VERSION)

mark_as_advanced(SIP_VERSION)
