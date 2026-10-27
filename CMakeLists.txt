cmake_minimum_required(VERSION 3.20)
project(moon_patrol_nd LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(SDL3 REQUIRED CONFIG REQUIRED COMPONENTS SDL3)
find_package(SDL3_image REQUIRED CONFIG)

file(GLOB_RECURSE SOURCES CONFIGURE_DEPENDS src/*.cpp)

add_executable(moon_patrol_nd ${SOURCES})

target_include_directories(moon_patrol_nd PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_SOURCE_DIR}/third_party
)

target_link_libraries(moon_patrol_nd PRIVATE SDL3::SDL3 SDL3_image::SDL3_image)

if(APPLE)
    set_target_properties(moon_patrol_nd PROPERTIES MACOSX_BUNDLE TRUE)
endif()
