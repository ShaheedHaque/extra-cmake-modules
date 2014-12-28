macro(assert_var_defined varname)
    if(NOT DEFINED ${varname})
        message(SEND_ERROR "${varname} is not defined.")
    endif()
endmacro()

macro(assert_vars_strequal varname exp_varname)
    if(ARGC LESS 3 OR NOT "${ARGV2}" STREQUAL "ALLOW_UNDEFINED")
        assert_var_defined(${varname})
    endif()
    if(NOT ${varname} STREQUAL ${exp_varname})
        message(SEND_ERROR "${varname} is '${${varname}}', expecting '${${exp_varname}}'.")
    endif()
endmacro()

macro(assert_var_str_value varname value)
    if(ARGC LESS 3 OR NOT "${ARGV2}" STREQUAL "ALLOW_UNDEFINED")
        assert_var_defined(${varname})
    endif()
    set(_value_var "${value}")
    if(NOT ${varname} STREQUAL _value_var)
        message(SEND_ERROR "${varname} is '${${varname}}', expecting '${value}'.")
    endif()
endmacro()

macro(assert_var_num_value varname value)
    if(ARGC LESS 3 OR NOT "${ARGV2}" STREQUAL "ALLOW_UNDEFINED")
        assert_var_defined(${varname})
    endif()
    set(_value_var "${value}")
    if(NOT ${varname} EQUAL _value_var)
        message(SEND_ERROR "${varname} is '${${varname}}', expecting '${value}'.")
    endif()
endmacro()

macro(assert_var_bool_value varname value)
    if(ARGC LESS 3 OR NOT "${ARGV2}" STREQUAL "ALLOW_UNDEFINED")
        assert_var_defined(${varname})
    endif()
    if(${value} AND NOT ${varname})
        message(SEND_ERROR "${varname} was FALSE")
    elseif(${varname} AND NOT ${value})
        message(SEND_ERROR "${varname} was TRUE")
    endif()
endmacro()

macro(assert_var_relative_path varname)
    if(ARGC LESS 2 OR NOT "${ARGV1}" STREQUAL "ALLOW_UNDEFINED")
        assert_var_defined(${varname})
    endif()
    if(DEFINED ${varname} AND IS_ABSOLUTE "${${varname}}")
        message(SEND_ERROR "${varname} (${${varname}}) should be a relative path, but is absolute.")
    endif()
endmacro()

macro(assert_var_absolute_path varname)
    if(ARGC LESS 2 OR NOT "${ARGV1}" STREQUAL "ALLOW_UNDEFINED")
        assert_var_defined(${varname})
    endif()
    if(DEFINED ${varname} AND NOT IS_ABSOLUTE "${${varname}}")
        message(SEND_ERROR "${varname} (${${varname}}) should be an absolute path, but is relative.")
    endif()
endmacro()
