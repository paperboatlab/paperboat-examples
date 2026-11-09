# A polyphonic Eurorack-style synthesizer: vector CV/gate wires [6], a ladder-ish low-pass
# filter and a multi-channel Scope. Native C++ linking the engine's toolkit.
cmake_minimum_required(VERSION 3.25)
project(paperboat_modular_synth LANGUAGES CXX)

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
if(NOT PAPERBOAT_ENGINE_DIR)
  message(FATAL_ERROR "No Paperboat engine found: set PAPERBOAT_ENGINE_DIR")
endif()
set(PAPERBOAT_ENGINE_DIR "${PAPERBOAT_ENGINE_DIR}" CACHE PATH "Paperboat engine sources")
add_subdirectory(${PAPERBOAT_ENGINE_DIR} paperboat EXCLUDE_FROM_ALL)

add_executable(paperboat-modular-synth main.cpp domain/synth.cpp)
target_link_libraries(paperboat-modular-synth PRIVATE paperboat::core paperboat_warnings)
target_compile_definitions(paperboat-modular-synth PRIVATE
  PAPERBOAT_DESCRIPTOR="${CMAKE_CURRENT_SOURCE_DIR}/descriptor.toml")
