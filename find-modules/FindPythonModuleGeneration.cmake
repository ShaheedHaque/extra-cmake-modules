
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

find_program(SIP_COMMAND sip)

if(NOT SIP_COMMAND)
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

list(FIND _SIP_Qt5_VERSIONS "Qt_5_${Qt5Core_VERSION_MINOR}_${Qt5Core_VERSION_PATCH}" _SIP_Qt5_Version_Index)

if(_SIP_Qt5_Version_Index EQUAL -1)
  set(PythonModuleGeneration_FOUND FALSE)
  return()
endif()

set(PythonModuleGeneration_FOUND TRUE)

include(CMakeParseArguments)

set(GPB_MODULE_DIR ${CMAKE_CURRENT_LIST_DIR})

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

    set(generator_depends "${GPB_MODULE_DIR}/sip_generator.py" "${GPB_MODULE_DIR}/rules_engine.py" "${GPB_MODULE_DIR}/FindPythonModuleGeneration.cmake")

    foreach(dep ${GPB_SIP_DEPENDS})
        if (IS_ABSOLUTE ${dep})
          list(APPEND generator_depends "${dep}")
        endif()
        file(APPEND "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}/${modulename_value}mod.sip"
          "%Import ${dep}\n\n")
    endforeach()

    set(sip_files)
    set(commands)

    if (GPB_RULES_FILE)
      set(rules_arg --project-rules ${GPB_RULES_FILE})
      list(APPEND generator_depends ${GPB_RULES_FILE})
    endif()

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

        add_custom_command(OUTPUT ${sip_file}
            COMMAND python ${GPB_MODULE_DIR}/sip_generator.py
              ${rules_arg}
              --includes $<JOIN:$<TARGET_PROPERTY:${target_value},INTERFACE_INCLUDE_DIRECTORIES>,,>
              --include_filename "${hdr_filename}"
              "${hdr_file}" > "${sip_file}"
            DEPENDS ${hdr_file} ${generator_depends}
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

    if (GPB_SIP_INCLUDES)
      set(sip_includes -I "$<JOIN:${GPB_SIP_INCLUDES},-I>")
    endif()
    foreach(path ${CMAKE_PREFIX_PATH} ${CMAKE_INSTALL_PREFIX} ${GPB_SIP_INCLUDES})
      if (EXISTS ${path}/share/sip)
        list(APPEND sip_includes -I "${path}/share/sip")
      endif()
    endforeach()

    set(GPB_Qt5_Tag -t Qt_5_${Qt5Core_VERSION_MINOR}_${Qt5Core_VERSION_PATCH})
    set(GPB_WS_Tag -t WS_X11)

    add_custom_target(generate_${modulename_value}_sip_files ALL DEPENDS ${sip_files})

    add_custom_command(OUTPUT
      "${CMAKE_CURRENT_BINARY_DIR}/pybuild/${pythonnamespace_value}/${modulename_value}/unified${modulename_value}.cpp"
      COMMAND python "${GPB_MODULE_DIR}/run-sip.py" --sip /usr/bin/sip
       --unify "${CMAKE_CURRENT_BINARY_DIR}/pybuild/${pythonnamespace_value}/${modulename_value}/unified${modulename_value}.cpp"
       --module-name "${modulename_value}"
       -c "${CMAKE_CURRENT_BINARY_DIR}/pybuild/${pythonnamespace_value}/${modulename_value}"
       -b "${CMAKE_CURRENT_BINARY_DIR}/pybuild/${pythonnamespace_value}/${modulename_value}/module.sbf"

       # TODO: What is this stuff?
       -x VendorID -x Py_v3

       ${GPB_WS_Tag} ${GPB_Qt5_Tag}

       -I "/usr/share/sip/PyQt5"
       -I "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}"
       ${sip_includes}
       "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}/${modulename_value}mod.sip"
       DEPENDS generate_${modulename_value}_sip_files "${GPB_MODULE_DIR}/run-sip.py"
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
        target_compile_definitions(Py${pyversion}KF5${modulename_value} PRIVATE _FORTIFY_SOURCE=2)
        target_include_directories(Py${pyversion}KF5${modulename_value} PRIVATE ${GPB_SIP_INCLUDES})
        target_link_libraries(Py${pyversion}KF5${modulename_value} PRIVATE -Wl,-Bsymbolic-functions -Wl,-z,relro)

        set_property(TARGET Py${pyversion}KF5${modulename_value} PROPERTY AUTOMOC OFF)
        set_property(TARGET Py${pyversion}KF5${modulename_value} PROPERTY OUTPUT_NAME py${pyversion}/${pythonnamespace_value}/${modulename_value})

        install(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/py${pyversion}/${pythonnamespace_value}
            DESTINATION lib/python${pyversion${pyversion}_maj_min}/dist-packages)
        install(FILES ${sip_files} "${CMAKE_CURRENT_BINARY_DIR}/sip/${pythonnamespace_value}/${modulename_value}/${modulename_value}mod.sip"
          DESTINATION share/sip/${pythonnamespace_value}/${modulename_value}
        )
    endforeach()
endfunction()
