add_executable(openyamm
    main.cpp
    GameApplication.cpp
)

target_include_directories(openyamm
    PRIVATE
        ${CMAKE_SOURCE_DIR}
)

target_link_libraries(openyamm
    PRIVATE
        openyamm_engine
)

target_compile_features(openyamm PRIVATE cxx_std_20)
