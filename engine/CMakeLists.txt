cmake_minimum_required(VERSION 3.19)
project(dsirb_demo C)
if(MSVC)
 set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif()
enable_testing()
set(RC_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../third_party/rcheevos")
if(NOT EXISTS "${RC_ROOT}/include/rc_runtime.h")
  message(FATAL_ERROR "Clone official rcheevos at the documented commit first.")
endif()
find_package(Git REQUIRED)
execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${RC_ROOT}" rev-parse HEAD
  OUTPUT_VARIABLE RC_HEAD OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY)
if(NOT RC_HEAD STREQUAL "1433173220a7eaede6a9ed7a18e94117be1821e0")
  message(FATAL_ERROR "Unexpected rcheevos HEAD; review/pin before building")
endif()
file(GLOB RC_RUNTIME "${RC_ROOT}/src/rcheevos/*.c")
add_library(rc_runtime STATIC ${RC_RUNTIME}
  "${RC_ROOT}/src/rc_compat.c" "${RC_ROOT}/src/rc_util.c" "${RC_ROOT}/src/rhash/md5.c")
target_include_directories(rc_runtime PUBLIC "${RC_ROOT}/include" PRIVATE "${RC_ROOT}/src")
target_compile_definitions(rc_runtime PRIVATE RC_DISABLE_LUA)
set_property(TARGET rc_runtime PROPERTY C_STANDARD 99)
add_executable(dsirb_demo demo.c)
target_link_libraries(dsirb_demo PRIVATE rc_runtime)
if(NOT WIN32)
 target_link_libraries(dsirb_demo PRIVATE m)
endif()
add_test(NAME controlled_conditions_and_measured COMMAND dsirb_demo)

add_executable(dsirb_live live_demo.c)
target_link_libraries(dsirb_live PRIVATE rc_runtime)
if(NOT WIN32)
 target_link_libraries(dsirb_live PRIVATE m)
endif()

add_executable(dsirb_wire ../tests/wire-golden.c)
target_include_directories(dsirb_wire PRIVATE ../dsi/network/include)

add_executable(dsirb_tx_queue ../tests/tx-queue-031.c)
add_test(NAME transmitter_queue_no_retry COMMAND dsirb_tx_queue)

add_executable(dsirb_sender ../tests/reliable-sender-cli.c)
add_executable(dsirb_reliable_test ../tests/reliable-sender-test.c)
add_test(NAME reliable_sender_bounds_loss_wrap COMMAND dsirb_reliable_test)

# 033 additive: official read-only NDS hash. Existing runtime targets unchanged.
add_library(rc_nds_hash STATIC
 "${RC_ROOT}/src/rhash/hash.c" "${RC_ROOT}/src/rhash/hash_rom.c"
 "${RC_ROOT}/src/rhash/md5.c" "${RC_ROOT}/src/rc_compat.c" "${RC_ROOT}/src/rc_util.c")
target_include_directories(rc_nds_hash PUBLIC "${RC_ROOT}/include" PRIVATE "${RC_ROOT}/src")
target_compile_definitions(rc_nds_hash PRIVATE RC_HASH_NO_DISC RC_HASH_NO_ZIP RC_HASH_NO_ENCRYPTED)
add_executable(dsirb_nds_hash nds_hash_033.c)
target_link_libraries(dsirb_nds_hash PRIVATE rc_nds_hash)
