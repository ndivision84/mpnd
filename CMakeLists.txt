cmake_minimum_required(VERSION 3.20)
project(moon_patrol_nd LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(SDL3 REQUIRED CONFIG REQUIRED COMPONENTS SDL3)

file(GLOB_RECURSE SOURCES CONFIGURE_DEPENDS src/*.cpp)

add_executable(moon_patrol_nd ${SOURCES})

target_include_directories(moon_patrol_nd PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}/include
    ${CMAKE_CURRENT_SOURCE_DIR}/src
)

target_link_libraries(moon_patrol_nd PRIVATE SDL3::SDL3)

add_custom_command(TARGET moon_patrol_nd POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
        ${CMAKE_CURRENT_SOURCE_DIR}/assets
        $<TARGET_FILE_DIR:moon_patrol_nd>/assets
)

if(APPLE)
    set_target_properties(moon_patrol_nd PROPERTIES MACOSX_BUNDLE TRUE)
endif()
