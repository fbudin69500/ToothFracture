cmake_minimum_required(VERSION 3.0)

find_package(ITK REQUIRED)
include(${ITK_USE_FILE})


add_executable(ToothFractureSimulation ToothFractureSimulation.cxx)

target_link_libraries(ToothFractureSimulation ${ITK_LIBRARIES})
set_property(TARGET ToothFractureSimulation PROPERTY CXX_STANDARD 11)
