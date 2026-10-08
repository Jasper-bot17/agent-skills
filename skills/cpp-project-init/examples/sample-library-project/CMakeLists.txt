cmake_minimum_required(VERSION 3.14)
project(demo-lib VERSION 1.0.0 LANGUAGES CXX)

# C++ 标准
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# 构建类型
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# 编译器警告选项
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    add_compile_options(
        -Wall
        -Wextra
        -Wpedantic
        -Wshadow
        -Wnon-virtual-dtor
    )
elseif(MSVC)
    add_compile_options(/W4 /permissive-)
endif()

# 输出目录
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# 静态库目标
add_library(demo-lib STATIC
    src/demo_lib.cpp
)
target_include_directories(demo-lib PUBLIC include)
target_compile_definitions(demo-lib PRIVATE DEMO_LIB_EXPORTS)

# 单元测试
enable_testing()
add_subdirectory(tests)

# 安装规则
install(TARGETS demo-lib ARCHIVE DESTINATION lib)
install(DIRECTORY include/ DESTINATION include)

