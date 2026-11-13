# A high-speed train pantograph on a compliant catenary: multibody dynamics, aerodynamic
# uplift and an active pneumatic contact-force regulator. Native C++ linking the engine.
cmake_minimum_required(VERSION 3.25)
project(paperboat_train_pantograph LANGUAGES CXX)

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

add_executable(paperboat-train-pantograph main.cpp domain/pantograph.cpp)
target_link_libraries(paperboat-train-pantograph PRIVATE paperboat::core paperboat_warnings)
target_compile_definitions(paperboat-train-pantograph PRIVATE
  PAPERBOAT_DESCRIPTOR="${CMAKE_CURRENT_SOURCE_DIR}/descriptor.toml")
