# A Paperboat backend as a project of its own (see ../cart-pole-cpp/CMakeLists.txt): it
# uses the engine and its optional opencv package, so it needs OpenCV.
cmake_minimum_required(VERSION 3.25)
project(paperboat_parts LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

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

set(PARTS_SOURCES main.cpp)
if(TARGET paperboat::toolkit_opencv)
  list(APPEND PARTS_SOURCES domain/count.cpp)
endif()

add_executable(paperboat-parts ${PARTS_SOURCES})
target_link_libraries(paperboat-parts PRIVATE paperboat::core paperboat_warnings)
target_compile_definitions(paperboat-parts PRIVATE
  PAPERBOAT_DESCRIPTOR="${CMAKE_CURRENT_SOURCE_DIR}/descriptor.toml")

if(TARGET paperboat::toolkit_opencv)
  target_link_libraries(paperboat-parts PRIVATE paperboat::toolkit_opencv)
  target_compile_definitions(paperboat-parts PRIVATE PAPERBOAT_HAS_OPENCV=1)
endif()
