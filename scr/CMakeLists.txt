cmake_minimum_required(VERSION 3.20)
project(OpenSteamTool VERSION 1.0.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_C_STANDARD 11)

# Allow CMAKE_MSVC_RUNTIME_LIBRARY to control runtime selection for all targets,
# including dependencies pulled in via FetchContent.
if(POLICY CMP0091)
    cmake_policy(SET CMP0091 NEW)
endif()

# Use the static runtime everywhere so the resulting DLL has no extra runtime
# dependencies. This must be set BEFORE FetchContent_MakeAvailable so that the
# fetched dependencies (Lua, Detours) inherit it.
set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")

# Build dependencies as static libraries.
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)

include(FetchContent)

# ---------------------------------------------------------------------------
# Lua 5.5 (built from the official source release)
# ---------------------------------------------------------------------------
FetchContent_Declare(
    lua
    URL https://www.lua.org/ftp/lua-5.5.0.tar.gz
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    TLS_VERIFY OFF
)
FetchContent_MakeAvailable(lua)

# The Lua tarball ships only Makefiles, so we build a static library here.
file(GLOB LUA_CORE_SOURCES "${lua_SOURCE_DIR}/src/*.c")
list(REMOVE_ITEM LUA_CORE_SOURCES
    "${lua_SOURCE_DIR}/src/lua.c"
    "${lua_SOURCE_DIR}/src/luac.c")

add_library(lua_static STATIC ${LUA_CORE_SOURCES})
target_include_directories(lua_static PUBLIC "${lua_SOURCE_DIR}/src")
set_target_properties(lua_static PROPERTIES POSITION_INDEPENDENT_CODE ON)

# ---------------------------------------------------------------------------
# Microsoft Detours (the upstream repo has no CMake, so we build a static lib
# from its sources directly).
# ---------------------------------------------------------------------------
FetchContent_Declare(
    detours
    GIT_REPOSITORY https://github.com/microsoft/Detours.git
    GIT_TAG        main
    # SOURCE_SUBDIR points at a directory with no CMakeLists.txt so that
    # FetchContent_MakeAvailable downloads the source but does NOT add the
    # repo's own (Make-based) build into our project.
    SOURCE_SUBDIR  cmake-noop
)
FetchContent_MakeAvailable(detours)

# Pick the architecture-specific disassembler source.
if(CMAKE_SIZEOF_VOID_P EQUAL 8)
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "ARM|aarch64")
        set(DETOURS_ARCH_SRC "${detours_SOURCE_DIR}/src/disolarm64.cpp")
    else()
        set(DETOURS_ARCH_SRC "${detours_SOURCE_DIR}/src/disolx64.cpp")
    endif()
else()
    if(CMAKE_SYSTEM_PROCESSOR MATCHES "ARM|aarch64")
        set(DETOURS_ARCH_SRC "${detours_SOURCE_DIR}/src/disolarm.cpp")
    else()
        set(DETOURS_ARCH_SRC "${detours_SOURCE_DIR}/src/disolx86.cpp")
    endif()
endif()

add_library(detours STATIC
    ${detours_SOURCE_DIR}/src/detours.cpp
    ${detours_SOURCE_DIR}/src/modules.cpp
    ${detours_SOURCE_DIR}/src/disasm.cpp
    ${detours_SOURCE_DIR}/src/image.cpp
    ${detours_SOURCE_DIR}/src/creatwth.cpp
    ${DETOURS_ARCH_SRC}
)
target_include_directories(detours PUBLIC "${detours_SOURCE_DIR}/src")
set_target_properties(detours PROPERTIES POSITION_INDEPENDENT_CODE ON)

# Detours is MSVC-targeted C++; under clang-cl / GNU-style clang on Windows it
# still compiles, but we need to silence MSVC-specific warnings it emits.
if(MSVC)
    target_compile_options(detours PRIVATE /w)
else()
    target_compile_options(detours PRIVATE -w)
endif()

# ---------------------------------------------------------------------------
# OpenSteamTool (the actual hook DLL)
# ---------------------------------------------------------------------------
add_library(OpenSteamTool SHARED
    dllmain.cpp
    ByteSearch.cpp
    HookManager.cpp
    LuaConfig.cpp
)

target_include_directories(OpenSteamTool PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(OpenSteamTool PRIVATE
    lua_static
    detours
    winhttp
)

# ---------------------------------------------------------------------------
# dwmapi.dll HiJack Project
# ---------------------------------------------------------------------------
add_library(dwmapi SHARED
    dwmapi/dwmapi.cpp
)
