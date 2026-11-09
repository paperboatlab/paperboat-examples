# An air-hockey puck tracker: a synthetic overhead camera, the optional OpenCV toolkit's
# threshold/morphology/centroid blocks and a ballistic tracker. OpenCV is optional: without
# paperboat::toolkit_opencv the backend builds with `descriptor-degraded.toml`, a synthetic
# centroid path that runs the same graph shape.
cmake_minimum_required(VERSION 3.25)
project(paperboat_air_hockey LANGUAGES CXX)

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

# The optional OpenCV package: an installed copy under engine/toolkit/opencv, or the
# paperboat-toolkit-opencv checkout next to this repository.
if(NOT TARGET paperboat::toolkit_opencv)
  foreach(dir "${PAPERBOAT_ENGINE_DIR}/toolkit/opencv"
              "${CMAKE_CURRENT_LIST_DIR}/../../paperboat-toolkit-opencv/engine/toolkit/opencv")
    if(EXISTS "${dir}/CMakeLists.txt")
      add_subdirectory("${dir}" air-hockey-opencv)
      break()
    endif()
  endforeach()
endif()

add_executable(paperboat-air-hockey main.cpp domain/state.cpp domain/vision.cpp)
target_link_libraries(paperboat-air-hockey PRIVATE paperboat::core paperboat_warnings)
target_compile_definitions(paperboat-air-hockey PRIVATE
  PAPERBOAT_DESCRIPTOR="${CMAKE_CURRENT_SOURCE_DIR}/descriptor.toml"
  PAPERBOAT_DESCRIPTOR_DEGRADED="${CMAKE_CURRENT_SOURCE_DIR}/descriptor-degraded.toml")

if(TARGET paperboat::toolkit_opencv)
  target_link_libraries(paperboat-air-hockey PRIVATE paperboat::toolkit_opencv)
  target_compile_definitions(paperboat-air-hockey PRIVATE PAPERBOAT_HAS_OPENCV=1)
  message(STATUS "08-air-hockey-tracker-cpp: OpenCV pipeline enabled")
else()
  message(STATUS "08-air-hockey-tracker-cpp: OpenCV not found, degraded synthetic tracker")
endif()
