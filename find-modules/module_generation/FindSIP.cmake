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
#   SIP_INCLUDE_DIRS - Where to find sip.h.
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

#
# See https://github.com/pybind/pybind11/blob/master/tools/FindPythonLibsNew.cmake.
#
find_package(PythonInterp QUIET REQUIRED)
find_package(PythonLibs QUIET REQUIRED)
execute_process(
    COMMAND ${PYTHON_EXECUTABLE} -c "from distutils import sysconfig as s;import sys;import struct;
print('.'.join(str(v) for v in sys.version_info));
print(sys.prefix);
print(s.get_python_inc(plat_specific=True));
print(s.get_python_lib(plat_specific=True));
print(s.get_config_var('SO'));
print(hasattr(sys, 'gettotalrefcount')+0);
print(struct.calcsize('@P'));
print(s.get_config_var('LDVERSION') or s.get_config_var('VERSION'));
print(s.get_config_var('LIBDIR') or '');
print(s.get_config_var('MULTIARCH') or '');
"
    RESULT_VARIABLE _PYTHON_SUCCESS
    OUTPUT_VARIABLE _PYTHON_VALUES
    ERROR_VARIABLE _PYTHON_ERROR_VALUE)
#
# Convert the process output into a list.
#
string(REGEX REPLACE ";" "\\\\;" _PYTHON_VALUES ${_PYTHON_VALUES})
string(REGEX REPLACE "\n" ";" _PYTHON_VALUES ${_PYTHON_VALUES})
list(GET _PYTHON_VALUES 0 _PYTHON_VERSION_LIST)
list(GET _PYTHON_VALUES 1 PYTHON_PREFIX)
list(GET _PYTHON_VALUES 2 PYTHON_INCLUDE_DIR)
list(GET _PYTHON_VALUES 3 PYTHON_SITE_PACKAGES)
list(GET _PYTHON_VALUES 4 PYTHON_MODULE_EXTENSION)
list(GET _PYTHON_VALUES 5 PYTHON_IS_DEBUG)
list(GET _PYTHON_VALUES 6 PYTHON_SIZEOF_VOID_P)
list(GET _PYTHON_VALUES 7 PYTHON_LIBRARY_SUFFIX)
list(GET _PYTHON_VALUES 8 PYTHON_LIBDIR)
list(GET _PYTHON_VALUES 9 PYTHON_MULTIARCH)
#
# Find sip.h.
#
find_file(SIP_HEADER NAMES sip.h
            HINTS "${PYTHON_INCLUDE_DIR}")
if(SIP_HEADER)
    set(SIP_INCLUDE_DIRS ${PYTHON_INCLUDE_DIR})
    file(STRINGS "${SIP_HEADER}" SIP_VERSION_TMP REGEX ".*SIP_VERSION_STR.*\"\([0-9]+.[0-9]+\.*)\"")
    string(REGEX REPLACE ".*SIP_VERSION_STR.*\"\([0-9]+.[0-9]+\.*)\"" "\\1" SIP_VERSION_TMP "${SIP_VERSION_TMP}")
    set(SIP_HEADER_VERSION ${SIP_VERSION_TMP} CACHE STRING "LibSIP version" FORCE)
    if(NOT SIP_VERSION STREQUAL SIP_HEADER_VERSION)
      message(SEND_ERROR "Command version \"${SIP_VERSION}\" does not match header version ${SIP_HEADER_VERSION}")
    endif()
endif()

include(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(SIP REQUIRED_VARS SIP_EXECUTABLE SIP_INCLUDE_DIRS
                                      VERSION_VAR SIP_VERSION)

mark_as_advanced(SIP_VERSION)
