# A Paperboat backend as a project of its own: it uses the engine, the engine doesn't know
# it. Copy this folder anywhere and point PAPERBOAT_ENGINE_DIR at a Paperboat engine.
cmake_minimum_required(VERSION 3.25)
project(paperboat_cart_pole LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# The engine (paperboat::core, which brings paperboat::toolkit). Until the engine installs
# a CMake package (TODO), a backend builds it from source; only the libraries it links
# are built, not the engine's tests or tools.
# The engine: -DPAPERBOAT_ENGINE_DIR=…, else the Paperboat repo this sits in, else a
# paperboat checkout next to the paperboat-examples one.
if(NOT PAPERBOAT_ENGINE_DIR)
  foreach(dir "${CMAKE_CURRENT_LIST_DIR}/../../../engine" "${CMAKE_CURRENT_LIST_DIR}/../../paperboat/engine")
    if(EXISTS "${dir}/CMakeLists.txt")
      set(PAPERBOAT_ENGINE_DIR "${dir}")
      break()
    endif()
  endforeach()
endif()
if(NOT PAPERBOAT_ENGINE_DIR)
  message(FATAL_ERROR "No Paperboat engine: clone paperboat next to paperboat-examples, or set PAPERBOAT_ENGINE_DIR")
endif()
set(PAPERBOAT_ENGINE_DIR "${PAPERBOAT_ENGINE_DIR}" CACHE PATH "Paperboat engine sources")
add_subdirectory(${PAPERBOAT_ENGINE_DIR} paperboat EXCLUDE_FROM_ALL)

add_executable(paperboat-cart-pole main.cpp)
target_link_libraries(paperboat-cart-pole PRIVATE paperboat::core paperboat_warnings)
target_compile_definitions(paperboat-cart-pole PRIVATE
  PAPERBOAT_DESCRIPTOR="${CMAKE_CURRENT_SOURCE_DIR}/descriptor.toml")
