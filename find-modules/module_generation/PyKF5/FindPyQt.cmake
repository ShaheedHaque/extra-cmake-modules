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
# FindPyQt
# --------
#
# Find PyQt
#
# This module finds an installed PyQt.  It sets the following variables:
#
# ::
#
#   PyQt_FOUND - set to true if PyQt is found
#   PyQt_DIR - the directory where PyQt is installed
#   PyQt_CORE_MODULE - the PyQt QtCoremod.sip file
#   PyQt_VERSION - the version number of the PyQt installation
#
#
#
# The minimum required version of PyQt can be specified using the
# standard syntax, e.g.  find_package(PyQt 4.19)
#
# All information is collected from the PyQt_CORE_MODULE so the version
# to be found can be changed from the command line by means of setting
# PyQt_CORE_MODULE.

find_file(PyQt_CORE_MODULE QtCoremod.sip /usr/share/sip/PyQt5/QtCore)

if(PyQt_CORE_MODULE)
  file(STRINGS ${PyQt_CORE_MODULE} timeline REGEX "%Timeline[^{]*{[^}]+}" NEWLINE_CONSUME)
  if(timeline STREQUAL "")
    message(SEND_ERROR "No %Timeline in \"${PyQt_CORE_MODULE}\"")
  else()
    string(REGEX REPLACE ".*%Timeline[^{]*{([^}]+)}.*" "\\1" timeline ${timeline})
    string(REGEX REPLACE "[\n\r]+" "" timeline ${timeline})
    string(REGEX REPLACE " +" " " timeline ${timeline})
    separate_arguments(timeline)
    foreach(tag ${timeline})
      # Skip to the last tag, and extract the version number.
      string(REGEX REPLACE "Qt_([0-9]+)_([0-9]+)_([0-9]+)" "\\1.\\2.\\3" tag ${tag})
      set(PyQt_VERSION ${tag} CACHE STRING "PyQt version" FORCE)
    endforeach()
    get_filename_component(PyQt_INCLUDE_DIRS ${PyQt_CORE_MODULE} DIRECTORY)
    get_filename_component(PyQt_INCLUDE_DIRS ${PyQt_INCLUDE_DIRS} DIRECTORY)
  endif()
endif()

include(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(PyQt REQUIRED_VARS PyQt_INCLUDE_DIRS
                                       VERSION_VAR PyQt_VERSION)

mark_as_advanced(PyQt_VERSION)
