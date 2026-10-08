# Google Test 通过 FetchContent 获取
include(FetchContent)
FetchContent_Declare(
    googletest
    GIT_REPOSITORY https://github.com/google/googletest.git
    GIT_TAG v1.14.0
)
# 防止 Google Test 覆盖父项目的编译器/链接器设置
set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
FetchContent_MakeAvailable(googletest)

add_executable(tests test_demo_app.cpp)
target_link_libraries(tests PRIVATE GTest::gtest_main)
target_include_directories(tests PRIVATE ${CMAKE_SOURCE_DIR}/include)
target_sources(tests PRIVATE ${CMAKE_SOURCE_DIR}/src/demo_app.cpp)

include(GoogleTest)
gtest_discover_tests(tests)

