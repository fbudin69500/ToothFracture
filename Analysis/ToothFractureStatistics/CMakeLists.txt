cmake_minimum_required(VERSION 2.8.9)

project(ToothFractureStatistics)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/ToothFractureStatistics")
set(EXTENSION_CATEGORY "ToothFracture")
set(EXTENSION_CONTRIBUTORS "Hina Shah (Kitware Inc.)")
set(EXTENSION_DESCRIPTION "This is an extension to analyse the quality of automatic tooth fracture detection via isolated wavelets in CBCT. ")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/ToothFractureStatistics.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/ToothFractureStatistics/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(ToothFractureStatistics)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
