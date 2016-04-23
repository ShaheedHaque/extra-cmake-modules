#=============================================================================
# Copyright 2016 Stephen Kelly <steveire@gmail.com>
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
#=============================================================================


macro(find_python version _CURRENT_VERSION)
  find_library(PYTHON${version}_LIBRARY
    NAMES
      python${_CURRENT_VERSION}mu
      python${_CURRENT_VERSION}m
      python${_CURRENT_VERSION}u
      python${_CURRENT_VERSION}
    PATHS
      [HKEY_LOCAL_MACHINE\\SOFTWARE\\Python\\PythonCore\\${_CURRENT_VERSION}\\InstallPath]/libs
      [HKEY_CURRENT_USER\\SOFTWARE\\Python\\PythonCore\\${_CURRENT_VERSION}\\InstallPath]/libs
    # Avoid finding the .dll in the PATH.  We want the .lib.
    NO_SYSTEM_ENVIRONMENT_PATH
  )

  if(PYTHON${version}_LIBRARY)
    # Use the library's install prefix as a hint
    set(_Python_INCLUDE_PATH_HINT)
    get_filename_component(_Python_PREFIX ${PYTHON${version}_LIBRARY} PATH)
    get_filename_component(_Python_PREFIX ${_Python_PREFIX} PATH)
    if(_Python_PREFIX)
      set(_Python_INCLUDE_PATH_HINT ${_Python_PREFIX}/include)
    endif()
    unset(_Python_PREFIX)

    find_path(PYTHON${version}_INCLUDE_DIR
      NAMES Python.h
      HINTS
        ${_Python_INCLUDE_PATH_HINT}
      PATHS
        [HKEY_LOCAL_MACHINE\\SOFTWARE\\Python\\PythonCore\\${_CURRENT_VERSION}\\InstallPath]/include
        [HKEY_CURRENT_USER\\SOFTWARE\\Python\\PythonCore\\${_CURRENT_VERSION}\\InstallPath]/include
      PATH_SUFFIXES
        python${_CURRENT_VERSION}mu
        python${_CURRENT_VERSION}m
        python${_CURRENT_VERSION}u
        python${_CURRENT_VERSION}
    )
  endif()

  find_program(GPB_PYTHON${version}_COMMAND python${version})

  if(PYTHON${version}_LIBRARY AND PYTHON${version}_INCLUDE_DIR AND EXISTS "${PYTHON${version}_INCLUDE_DIR}/patchlevel.h")
    list(APPEND _pyversions ${version})

    file(STRINGS "${PYTHON${version}_INCLUDE_DIR}/patchlevel.h" python_version_define
         REGEX "^#define[ \t]+PY_MINOR_VERSION[ \t]+[0-9]+")
    string(REGEX REPLACE "^#define[ \t]+PY_MINOR_VERSION[ \t]+([0-9]+)" "\\1"
                         min_ver "${python_version_define}")
    unset(python_version_define)

    set(pyversion${version}_maj_min ${version}.${min_ver})

    add_library(Python::Libs${version} UNKNOWN IMPORTED)
    set_property(TARGET Python::Libs${version} PROPERTY IMPORTED_LOCATION ${PYTHON${version}_LIBRARY})
    set_property(TARGET Python::Libs${version} PROPERTY INTERFACE_INCLUDE_DIRECTORIES ${PYTHON${version}_INCLUDE_DIR})
    break()
  endif()
endmacro()

if (NOT Qt5Core_VERSION_MINOR OR NOT Qt5Core_VERSION_PATCH)
  set(PythonModuleGeneration_FOUND FALSE)
  return()
endif()

set(_PYTHON2_VERSIONS 2.7 2.6 2.5 2.4 2.3 2.2 2.1 2.0)
set(_PYTHON3_VERSIONS 3.6 3.5 3.4 3.3 3.2 3.1 3.0)

foreach(_CURRENT_VERSION ${_PYTHON3_VERSIONS})
  find_python(3 ${_CURRENT_VERSION})
endforeach()

foreach(_CURRENT_VERSION ${_PYTHON2_VERSIONS})
  find_python(2 ${_CURRENT_VERSION})
endforeach()

if(NOT _pyversions)
  set(PythonModuleGeneration_FOUND FALSE)
  return()
endif()

find_program(GBP_SIP_COMMAND sip)

if(NOT GBP_SIP_COMMAND)
  set(PythonModuleGeneration_FOUND FALSE)
  return()
endif()

if(NOT GPB_PYTHON2_COMMAND)
  set(PythonModuleGeneration_FOUND FALSE)
  return()
endif()

execute_process(
  COMMAND ${GPB_PYTHON2_COMMAND} ${CMAKE_CURRENT_LIST_DIR}/sip_generation/sip_generator.py --self-check
  RESULT_VARIABLE selfCheckErrors
)

if (selfCheckErrors)
  set(PythonModuleGeneration_FOUND FALSE)
  return()
endif()

find_file(SIP_Qt5Core_Mod_FILE
  NAMES QtCoremod.sip
  PATH_SUFFIXES share/sip/PyQt5/QtCore
)

if(NOT SIP_Qt5Core_Mod_FILE)
  set(PythonModuleGeneration_FOUND FALSE)
  return()
endif()

file(STRINGS "${SIP_Qt5Core_Mod_FILE}" _SIP_Qt5_VERSIONS
  REGEX "^%Timeline"
)

string(REGEX MATCHALL "Qt_5_[^ }]+" _SIP_Qt5_VERSIONS "${_SIP_Qt5_VERSIONS}")

set(GPB_Qt5_Tag Qt_5_${Qt5Core_VERSION_MINOR}_${Qt5Core_VERSION_PATCH})

list(FIND _SIP_Qt5_VERSIONS ${GPB_Qt5_Tag} _SIP_Qt5_Version_Index)

if(_SIP_Qt5_Version_Index EQUAL -1)
  set(PythonModuleGeneration_FOUND FALSE)
  return()
endif()

set(PythonModuleGeneration_FOUND TRUE)

include(CMakeParseArguments)

set(GPB_MODULE_DIR ${CMAKE_CURRENT_LIST_DIR})

function(_compute_implicit_include_dirs)
  execute_process(COMMAND ${CMAKE_CXX_COMPILER} -v -E -x c++ -
                  ERROR_VARIABLE _compilerOutput
                  OUTPUT_VARIABLE _compilerStdout
                  INPUT_FILE /dev/null)

  if( "${_compilerOutput}" MATCHES "> search starts here[^\n]+\n *(.+ *\n) *End of (search) list" )

    # split the output into lines and then remove leading and trailing spaces from each of them:
    string(REGEX MATCHALL "[^\n]+\n" _includeLines "${CMAKE_MATCH_1}")
    foreach(nextLine ${_includeLines})
      # on OSX, gcc says things like this:  "/System/Library/Frameworks (framework directory)", strip the last part
      string(REGEX REPLACE "\\(framework directory\\)" "" nextLineNoFramework "${nextLine}")
      # strip spaces at the beginning and the end
      string(STRIP "${nextLineNoFramework}" _includePath)
      list(APPEND _resultIncludeDirs "${_includePath}")
    endforeach()
  endif()

  set(_GPB_IMPLICIT_INCLUDE_DIRS ${_resultIncludeDirs} PARENT_SCOPE)
endfunction()

function(ecm_generate_python_binding
    target_keyword target_value
    pythonnamespace_keyword pythonnamespace_value
    modulename_keyword modulename_value
    )

    cmake_parse_arguments(GPB "" "RULES_FILE" "SIP_DEPENDS;SIP_INCLUDES;HEADERS"  ${ARGN})

    file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}/${modulename_value}mod.sip"
          "
%Module ${pythonnamespace_value}.${modulename_value}

%ModuleHeaderCode
#pragma GCC visibility push(default)
%End\n\n")

    set(generator_depends "${GPB_MODULE_DIR}/sip_generation/sip_generator.py"
        "${GPB_MODULE_DIR}/sip_generation/rules_engine.py"
        "${GPB_MODULE_DIR}/FindPythonModuleGeneration.cmake"
        "${GPB_MODULE_DIR}/sip_generation/PyQt_template_typecode.py"
        )

    if (NOT _GPB_IMPLICIT_INCLUDE_DIRS)
      _compute_implicit_include_dirs()
    endif()

    foreach(dep ${GPB_SIP_DEPENDS})
        if (IS_ABSOLUTE ${dep})
          list(APPEND generator_depends "${dep}")
        endif()
        file(APPEND "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}/${modulename_value}mod.sip"
          "%Import ${dep}\n\n")
    endforeach()

    set(sip_files)
    set(commands)

    if (NOT GPB_RULES_FILE)
      set(GPB_RULES_FILE "${GPB_MODULE_DIR}/Qt5Ruleset.py")
    endif()

    list(APPEND generator_depends ${GPB_RULES_FILE})

    foreach(hdr ${GPB_HEADERS})
        if (${hdr} MATCHES ".*.h$")
          continue()
        endif()
        get_filename_component(hdr ${hdr} NAME)
        string(TOLOWER ${hdr}.h hdr_filename)

        if (EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/${hdr_filename}")
          set(hdr_file "${CMAKE_CURRENT_SOURCE_DIR}/${hdr_filename}")
        else()
          file(GLOB hdr_file "${CMAKE_CURRENT_SOURCE_DIR}/*/${hdr_filename}")
        endif()

        set(sip_file "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}/${hdr}.sip")
        list(APPEND sip_files ${sip_file})

        set(inc_dirs "-I$<JOIN:$<TARGET_PROPERTY:${target_value},INTERFACE_INCLUDE_DIRECTORIES>;${_GPB_IMPLICIT_INCLUDE_DIRS},;-I>")
        set(comp_defs "-D$<JOIN:$<TARGET_PROPERTY:${target_value},INTERFACE_COMPILE_DEFINITIONS>,;-D>")

        foreach(stdVar 11 14)
          list(APPEND stdFlag "$<$<STREQUAL:$<TARGET_PROPERTY:${target_value},CXX_STANDARD>,${stdVar}>:${CMAKE_CXX${stdVar}_EXTENSION_COMPILE_OPTION}>")
        endforeach()

        set(comp_flags "$<JOIN:$<TARGET_PROPERTY:${target_value},INTERFACE_COMPILE_OPTIONS>;${stdFlag},;>")

        add_custom_command(OUTPUT ${sip_file}
            COMMAND ${GPB_PYTHON2_COMMAND} ${GPB_MODULE_DIR}/sip_generation/sip_generator.py
              --flags " ${inc_dirs};${comp_defs};${comp_flags}"
              --include_filename "${hdr_filename}"
              ${GPB_RULES_FILE}
              "${hdr_file}" > "${sip_file}"
            DEPENDS ${hdr_file} ${generator_depends}
            VERBATIM
        )

        file(APPEND "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}/${modulename_value}mod.sip"
          "%Include ${hdr}.sip\n")
    endforeach()

    file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/pybuild/${pythonnamespace_value}/${modulename_value}/module.sbf"
        "
target = ${modulename_value}
sources = sip${modulename_value}cmodule.cpp
headers = sipAPI${modulename_value}
"
    )

    get_filename_component(SIP_PYQT5_DIR ${SIP_Qt5Core_Mod_FILE} PATH)
    get_filename_component(SIP_PYQT5_DIR ${SIP_PYQT5_DIR} PATH)

    set(sip_includes -I "${SIP_PYQT5_DIR}")
    if (GPB_SIP_INCLUDES)
      list(APPEND sip_includes -I "$<JOIN:${GPB_SIP_INCLUDES},-I>")
    endif()
    foreach(path ${CMAKE_PREFIX_PATH} ${CMAKE_INSTALL_PREFIX})
      if (EXISTS ${path}/share/sip)
        list(APPEND sip_includes -I "${path}/share/sip")
      endif()
    endforeach()

    if (WIN32)
      set(GPB_WS_Tag -t WS_WIN)
    elif(APPLE)
      set(GPB_WS_Tag -t WS_MACX)
    else()
      set(GPB_WS_Tag -t WS_X11)
    endif()

    add_custom_target(generate_${modulename_value}_sip_files ALL DEPENDS ${sip_files})

    add_custom_command(OUTPUT
      "${CMAKE_CURRENT_BINARY_DIR}/pybuild/${pythonnamespace_value}/${modulename_value}/unified${modulename_value}.cpp"
      COMMAND ${GPB_PYTHON2_COMMAND} "${GPB_MODULE_DIR}/run-sip.py" --sip ${GBP_SIP_COMMAND}
       --unify "${CMAKE_CURRENT_BINARY_DIR}/pybuild/${pythonnamespace_value}/${modulename_value}/unified${modulename_value}.cpp"
       --module-name "${modulename_value}"
       -c "${CMAKE_CURRENT_BINARY_DIR}/pybuild/${pythonnamespace_value}/${modulename_value}"
       -b "${CMAKE_CURRENT_BINARY_DIR}/pybuild/${pythonnamespace_value}/${modulename_value}/module.sbf"
       -t ${GPB_Qt5_Tag} ${GPB_WS_Tag}

       # TODO: What is this stuff?
       -x VendorID -x Py_v3

       -I "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}"
       ${sip_includes}
       "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}/${modulename_value}mod.sip"
       DEPENDS generate_${modulename_value}_sip_files "${GPB_MODULE_DIR}/run-sip.py" ${generator_depends}
    )

    file(MAKE_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}"
         "${CMAKE_CURRENT_BINARY_DIR}/pybuild/${pythonnamespace_value}/${modulename_value}")

    foreach(pyversion ${_pyversions})
        file(MAKE_DIRECTORY
            "${CMAKE_CURRENT_BINARY_DIR}/py${pyversion}/${pythonnamespace_value}")
        execute_process(COMMAND "${CMAKE_COMMAND}" -E touch "${CMAKE_CURRENT_BINARY_DIR}/py${pyversion}/${pythonnamespace_value}/__init__.py")

        add_library(Py${pyversion}KF5${modulename_value} MODULE
          "${CMAKE_CURRENT_BINARY_DIR}/pybuild/${pythonnamespace_value}/${modulename_value}/unified${modulename_value}.cpp"
        )
        target_link_libraries(Py${pyversion}KF5${modulename_value} PRIVATE ${target_value} Python::Libs${pyversion})

        target_compile_options(Py${pyversion}KF5${modulename_value} PRIVATE -fstack-protector-strong -Wno-deprecated-declarations -Wno-overloaded-virtual)
        target_include_directories(Py${pyversion}KF5${modulename_value} PRIVATE ${GPB_SIP_INCLUDES})
        target_link_libraries(Py${pyversion}KF5${modulename_value} PRIVATE -Wl,-Bsymbolic-functions -Wl,-z,relro)

        set_property(TARGET Py${pyversion}KF5${modulename_value} PROPERTY AUTOMOC OFF)
        set_property(TARGET Py${pyversion}KF5${modulename_value} PROPERTY PREFIX "")
        set_property(TARGET Py${pyversion}KF5${modulename_value} PROPERTY OUTPUT_NAME py${pyversion}/${pythonnamespace_value}/${modulename_value})

        add_test(NAME Py${pyversion}Test COMMAND ${GPB_PYTHON${pyversion}_COMMAND} "${CMAKE_SOURCE_DIR}/autotests/pythontest.py" ${CMAKE_CURRENT_BINARY_DIR}/py${pyversion})

        # TODO: Add sanity test for generated sip module file

        install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/py${pyversion}/${pythonnamespace_value}
            DESTINATION lib/python${pyversion${pyversion}_maj_min}/dist-packages)
        install(FILES ${sip_files} "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}/${modulename_value}mod.sip"
          DESTINATION share/sip/${pythonnamespace_value}/${modulename_value}
        )
    endforeach()
endfunction()
