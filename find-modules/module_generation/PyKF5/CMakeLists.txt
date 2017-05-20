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
#       "CXX_SOURCES": {
#           "KF5Activities": {
#               "LIBRARIES": "/usr/lib/x86_64-linux-gnu/libKF5Activities.so.5.31.0",
#               "INCLUDE_DIRS": "/usr/include/KF5/KActivities;/usr/include/KF5"
#           },
#           ...
#           "$": null
#       },
#       "CXX_DEPENDENCIES": {
#           "Qt5Widgets": {
#               "LIBRARIES": ...,
#               "INCLUDE_DIRS": ...,
#           },
#           "$": null
#       },
#       "CXX_COMPILE_OPTIONS": "-fPIC,-std=gnu++14",
#       "SIP_DEPENDENCIES": "/usr/share/sip/PyQt5",
#       "CXX_SOURCE_ROOT": "/usr/include/KF5",
#       "PY_PACKAGE": "PyKF5",
#       "$": null
#   }
#
# The "$" dict entries are a convenience which the caller discards.
#

cmake_minimum_required(VERSION 3.7)

project(PyKF5)

set(CXX_SOURCES
        KF5Activities
        KF5ActivitiesStats
        KF5Akonadi
        KF5AkonadiCalendar
        KF5AkonadiContact
        KF5AkonadiMime
        KF5AkonadiNotes
        KF5AkonadiSearch
        KF5AkonadiSocialUtils
        KF5AlarmCalendar
        KF5Archive
        KF5Attica
        KF5Auth
        KF5BalooWidgets
        KF5Blog
        KF5BluezQt
        KF5Bookmarks
        KF5CalendarCore
        KF5CalendarSupport
        KF5CalendarUtils
        KF5Codecs
        KF5Completion
        KF5ComposerEditorNG
        KF5Config
        KF5ConfigWidgets
        KF5Contacts
        KF5CoreAddons
        KF5Crash
        KF5DBusAddons
        KF5Declarative
        KF5DesignerPlugin
        KF5DNSSD
        KF5DocTools
        KF5Emoticons
        KF5EventViews
        KF5FileMetaData
        KF5FollowupReminder
        KF5FrameworkIntegration
        KF5GAPI
        KF5GlobalAccel
        KF5Gpgmepp
        KF5GrantleeTheme
        KF5Gravatar
        KF5GuiAddons
        KF5Holidays
        KF5I18n
        KF5IconThemes
        KF5IdentityManagement
        KF5IdleTime
        KF5IMAP
        KF5IncidenceEditor
        KF5Init
        KF5ItemModels
        KF5ItemViews
        KF5JobWidgets
        KF5JS
        KF5JsEmbed
        KF5KaddressbookGrantlee
        KF5KCMUtils
        KF5KDcraw
#        KF5KDE4Support
        KF5KDEGames
#        KF5KDELibs4Support
        KF5KdepimDBusInterfaces
        KF5KDGantt2
        KF5KExiv2
        KF5KFace
        KF5KGeoMap
        KF5KHtml
        KF5KIO
        KF5Kipi
        KF5KMahjongglib
        KF5KontactInterface
        KF5Kross
        KF5Ldap
        KF5Libkdepim
        KF5Libkleo
        KF5LibKSieve
        KF5MailCommon
        KF5MailImporter
        KF5MailTransport
        KF5Mbox
        KF5MediaPlayer
        KF5MessageComposer
        KF5MessageCore
        KF5MessageList
        KF5MessageViewer
        KF5Mime
        KF5NetworkManagerQt
        KF5NewStuff
        KF5NewStuffCore
        KF5NewStuffQuick
        KF5Notifications
        KF5NotifyConfig
        KF5Package
        KF5Parts
        KF5People
        KF5PimCommon
        KF5PimTextEdit
        KF5Plasma
        KF5PlasmaQuick
        KF5Plotting
        KF5Prison
        KF5Pty
        KF5Runner
        KF5Sane
        KF5Screen
        KF5SendLater
        KF5Service
        KF5Solid
        KF5Sonnet
        KF5Su
        KF5Syndication
        KF5TemplateParser
        KF5TextEditor
        KF5TextWidgets
        KF5ThreadWeaver
        KF5Tnef
        KF5UnitConversion
        KF5Wallet
        KF5WebKit
        KF5WidgetsAddons
        KF5WindowSystem
        KF5XmlGui
        KF5XmlRpcClient)

set(CXX_DEPENDENCIES
        Qt5Widgets
        Qt5Xml)

#
# Find the list of targets for a KDE component.
#
function(get_kf5_targets component)
    set(file_glob  ${${component}_DIR}/*.cmake)
    file(GLOB target_files ${file_glob})
    foreach(f ${target_files})
        file(STRINGS ${f} targets REGEX "^ *add_library\\(.*\\) *")
        if(NOT targets STREQUAL "")
            foreach(target ${targets})
                string(REGEX REPLACE " *add_library\\(([^ \\)]+).*" "\\1" target ${target})
                if(TARGET ${target})
                    set(real_targets ${real_targets} ${target})
                else()
                    message(STATUS "Ignoring invalid target \"${target}\" for ${component} in ${f}")
                endif()
            endforeach()
        endif()
    endforeach()
    set(targets "${real_targets}" PARENT_SCOPE)
endfunction(get_kf5_targets)

#
# Find the list of targets for a Qt component.
#
function(get_qt5_targets component)
    string(REPLACE "Qt5" "Qt5::" target ${component})
    if(NOT TARGET ${target})
        message(STATUS "Ignoring invalid target \"${target}\" for ${component}")
        set(target "")
    endif()
    set(targets "${target}" PARENT_SCOPE)
endfunction(get_qt5_targets)

#
# Fetch a target property, recursing if necessary.
#
function(get_target_property_recursive target property)
    set(result)
    get_target_property(values ${target} ${property})
    if(values STREQUAL "values-NOTFOUND")
        # Skip
        message(STATUS "Warning: Target ${target} has no property ${property}")
    else()
        foreach(value ${values})
            string(FIND ${value} "$<TARGET_PROPERTY:" found)
            if(found EQUAL 0)
                #
                # Recurse. The format is:
                #
                # $<TARGET_PROPERTY:KF5::WebKit,INTERFACE_INCLUDE_DIRECTORIES>
                #
                string(REGEX REPLACE "\\$<TARGET_PROPERTY:(.*),(.*)>" "\\1" nested_tgt ${value})
                string(REGEX REPLACE "\\$<TARGET_PROPERTY:(.*),(.*)>" "\\2" nested_prop ${value})
                get_target_property_recursive(${nested_tgt} ${nested_prop})
                list(APPEND result ${get_target_property_recursive_result})
            else()
                list(APPEND result ${value})
            endif()
        endforeach()
    endif()
    set(get_target_property_recursive_result "${result}" PARENT_SCOPE)
endfunction(get_target_property_recursive)

#
# Find the includes, libraries etc. for a component.
#
function(get_targets_info dict component targets)
    if(targets STREQUAL "")
        message(STATUS "Warning: No targets for ${component}")
        return()
    endif()
    #
    # Make a combined list of includes, libraries etc.
    #
    set(libraries)
    set(includes)
    foreach(target ${targets})
        if(TARGET ${target})
            get_target_property(tmp ${target} LOCATION)
            list(APPEND libraries ${tmp})
            get_target_property_recursive(${target} INTERFACE_INCLUDE_DIRECTORIES)
            list(APPEND includes ${get_target_property_recursive_result})
        else()
            message(STATUS "Warning: Ignoring invalid target \"${target}\" in ${f}")
        endif()
    endforeach()
    #
    # De-duplicate and write results.
    #
    if(DEFINED includes)
        list(REMOVE_DUPLICATES includes)
        #
        # Not sure why the headers seem to include this.
        #
        list(REMOVE_ITEM includes "/usr/include")
    endif()
    file(APPEND "${dict}" "\"${component}\": {\n")
    file(APPEND "${dict}" "    \"LIBRARIES\": \"${libraries}\",\n")
    file(APPEND "${dict}" "    \"INCLUDE_DIRS\": \"${includes}\"\n")
    file(APPEND "${dict}" "},\n")
    set(includes "${includes}" PARENT_SCOPE)
endfunction(get_targets_info)

find_package(ECM REQUIRED NO_MODULE)
set(CMAKE_MODULE_PATH ${CMAKE_CURRENT_SOURCE_DIR} ${ECM_MODULE_PATH})
find_package(PyQt REQUIRED)
include(FeatureSummary)
#
# Write the values we found as a JSON blob.
#
set(dict ${CMAKE_CURRENT_BINARY_DIR}/configure.json)
message(STATUS "Writing ${dict}")
file(WRITE "${dict}" "{\n")
#
# Sources.
#
file(APPEND "${dict}" "\"CXX_SOURCES\": {\n")
foreach(component ${CXX_SOURCES})
    find_package(${component} REQUIRED)
    get_kf5_targets(${component})
    get_targets_info(${dict} ${component} "${targets}")
    #
    # Find the source root.
    #
    if(NOT DEFINED CXX_SOURCE_ROOT)
        foreach(include ${includes})
            if(include MATCHES ".*/KF5$")
                set(CXX_SOURCE_ROOT ${include})
                break()
            endif()
        endforeach()
    endif()
endforeach()
if(NOT DEFINED CXX_SOURCE_ROOT)
    message(SEND_ERROR "Unable to find CXX_SOURCE_ROOT")
    return()
endif()
#
# Write results.
#
file(APPEND "${dict}" "\"$\": null\n")
file(APPEND "${dict}" "},\n")
#
# Dependencies.
#
file(APPEND "${dict}" "\"CXX_DEPENDENCIES\": {\n")
foreach(component ${CXX_DEPENDENCIES})
    find_package(${component})
    get_qt5_targets(${component})
    get_targets_info(${dict} ${component} "${targets}")
endforeach()
file(APPEND "${dict}" "\"$\": null\n")
file(APPEND "${dict}" "},\n")
file(APPEND "${dict}" "\"CXX_COMPILE_OPTIONS\": \"-fPIC,-std=gnu++14\",\n")
file(APPEND "${dict}" "\"SIP_DEPENDENCIES\": \"${PyQt_INCLUDE_DIRS}\",\n")
file(APPEND "${dict}" "\"CXX_SOURCE_ROOT\": \"${CXX_SOURCE_ROOT}\",\n")
file(APPEND "${dict}" "\"SIP_PACKAGE\": \"${CMAKE_PROJECT_NAME}\",\n")
file(APPEND "${dict}" "\"$\": null\n")
file(APPEND "${dict}" "}\n")
unset(component)
unset(dict)
