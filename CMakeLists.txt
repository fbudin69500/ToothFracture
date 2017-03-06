cmake_minimum_required(VERSION 3.0)

find_package(ITK REQUIRED)
include(${ITK_USE_FILE})


add_executable(GenerateDisplacementField GenerateDisplacementField.cxx)

target_link_libraries(GenerateDisplacementField ${ITK_LIBRARIES})
set_property(TARGET GenerateDisplacementField PROPERTY CXX_STANDARD 11)
