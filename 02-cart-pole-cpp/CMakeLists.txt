cmake_minimum_required(VERSION 3.25)
project(paperboat_cart_pole LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT PAPERBOAT_ENGINE_DIR)
  foreach(dir "${CMAKE_CURRENT_LIST_DIR}/../../../engine" "${CMAKE_CURRENT_LIST_DIR}/../../paperboat/engine")
    if(EXISTS "${dir}/CMakeLists.txt")
      set(PAPERBOAT_ENGINE_DIR "${dir}")
      break()
    endif()
  endforeach()
endif()
if(PAPERBOAT_ENGINE_DIR)
  set(PAPERBOAT_ENGINE_DIR "${PAPERBOAT_ENGINE_DIR}" CACHE PATH "Paperboat engine sources")
  add_subdirectory(${PAPERBOAT_ENGINE_DIR} paperboat EXCLUDE_FROM_ALL)
else()
  # An installed paperboat: its SDK, with the toolkits `paperboat toolkit install` built as
  # paperboat::toolkit_<name> (paperboat#354).
  find_package(Paperboat 0.1 CONFIG REQUIRED)
  add_library(paperboat_warnings INTERFACE)
  target_link_libraries(paperboat_warnings INTERFACE paperboat::warnings)
endif()

# The optional toolkits this backend imports: control (the PID blocks) and the optimization
# toolkit its Workspace links. They are installed into the engine with
# `paperboat toolkit install optimization` and `paperboat toolkit install control`.
foreach(toolkit optimization control)
  if(NOT TARGET paperboat::toolkit_${toolkit})
    foreach(dir
        "${PAPERBOAT_ENGINE_DIR}/toolkit/${toolkit}"
        "${CMAKE_CURRENT_LIST_DIR}/../paperboat-toolkit-${toolkit}/engine/toolkit/${toolkit}")
      if(EXISTS "${dir}/toolkit.toml")
        add_subdirectory("${dir}" "${CMAKE_CURRENT_BINARY_DIR}/${toolkit}-toolkit")
        break()
      endif()
    endforeach()
  endif()
  if(NOT TARGET paperboat::toolkit_${toolkit})
    message(FATAL_ERROR "The ${toolkit} toolkit is not installed (paperboat toolkit install ${toolkit})")
  endif()
endforeach()

add_executable(paperboat-cart-pole main.cpp domain/cart_pole.cpp)
target_link_libraries(paperboat-cart-pole PRIVATE paperboat::core paperboat::toolkit_control paperboat::toolkit_optimization paperboat_warnings)
target_compile_definitions(paperboat-cart-pole PRIVATE
  PAPERBOAT_DESCRIPTOR="${CMAKE_CURRENT_SOURCE_DIR}/descriptor.toml")
