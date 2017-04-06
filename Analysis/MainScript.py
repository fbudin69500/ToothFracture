#!/usr/bin/env python

from ToothFractureRoutines import *

'''
This script runs Tooth fracture simulation and analysis on a set of directories given the plane equations at which the
 fractures are to be simulated

Steps for running the full pipeline:
* Prep the data for each case:
---- ToothCBCT.nnrd: has the grayscale image
---- ToothCBCT-label.nrrd: is the labelmap image with segmentation. Label 1: tooth, Label 2: is a set of grayscale values
                            that the fracture will be filled with after forming a distribution.
---- ToothCBCT-resampled.nrrd: is the resampled version of original grayscale. Will be used to do wavelet analysis on.

NOTE:
To generate resampled grayscale, you can simulate fracture first, which will give a resampled grid (grid_*.nrrd),
and use that as a reference volume in Slicer's 'Resample Scalar/Vector/DWI Volume', and ToothCBCT as input volume.

* Get ALL the dependencies as listed ToothFractureRoutines.py and ToothFractureROCAnalysis.py
* Setup the ToothFractureStatistics Slicer Extension.
* Set the parameters in this script AND adjust paths to tools in ToothFractureRoutines.py
* If you have setup Python virtual environment, start now
* Run this script once with simulateFractures True, and once with simulateFractures False
    Outputs: Wavelets and fracture simulated grayscale images
* Run the SlicerExtension: ToothFractureStatistics
    Input: The data directory (dataDirectory parameter below) with all the wavelets and grayscales calculated
    Output: A csv file
* Deactivate python virtual environment if started
* Run the ToothFractureROCAnalysis.py
    Input: CSV file generated in the previous step
    Output: ROC curve analysis plots.

'''


# Set directory names and plane equations for fracture simulation
# plane equation obtained from slicer using easyclip over the input image and target tooth
DataSetDict = {}
DataSetDict['CBCT_FB_2ndMolar_left'] = [ [ 0.0 , 0.0 , 1.0 , -21.7779791599 ],
                   [0.960189391059, 0.0447772320061, 0.275737797177, 20.7913901406],
                   [0.881835380307, 0.457810084008, 0.113032247695, 38.1997245286],
                   [-0.475218084857, 0.696086834128, -0.538173662658, 26.1265530322],
                   [0.205808735441, -0.823558891086, -0.528576879299, -15.2868925338],
                   [0.935508951822, -0.205383765667, -0.287472624544, 22.2754210759] ]
DataSetDict['CBCT_FB_2ndMolar_right'] = [
                    [0.82509566, -0.54488327, -0.14939671, -37.4382379],
                    [0.07718801, -0.96372105, 0.25550685, -42.7291106],
                    [ 0.62725712, -0.77861462,  0.01754335, -43.4109153],
                    [0.97845362, -0.06475392, 0.19604958, -31.54739134] ,
                    [0.25826124, 0.91028086, -0.32355817, 32.80492154] ,
                    [0.24756939, 0.01436527,  0.96876366, -24.09609874] ]
DataSetDict['009_CBCT_2ndMolar_left'] = [ [ -0.0672012870315 , -0.211500304398 , 0.975064925152 , -36.0238476089 ],
                    [ 0.135102148167 , -0.934715071054 , 0.328717425009 , -23.2819513164 ],
                    [ -0.194005426475 , 0.9516884812 , 0.238014556804 , 1.43603272319 ],
                    [ -0.759579444484 , 0.581239745799 , 0.291889406147 , -16.5918529806 ],
                    [ -0.984996466339 , 0.135448103049 , 0.106938172231 , -21.3770969943 ],
                   [ -0.668726047668 , -0.594942313128 , 0.445925013002 , -37.5610070345 ] ]
DataSetDict['009_CBCT_2ndMolar_right'] = [[ 0.0741786819285 , -0.0684909430675 , 0.994890201914 , -31.0637712962 ],
                    [ 0.112082053501 , -0.141129918759 , 0.983625924483 , -36.0592904608 ],
                    [ 0.140201902076 , -0.782549379033 , 0.606596979904 , -31.6411604633 ],
                    [ 0.918658462354 , -0.285465089988 , 0.273086638162 , -33.3659890749 ],
                    [ 0.0752009028835 , 0.822910922179 , -0.563171766305 , 25.6816588054 ],
                    [ -0.87156715147 , -0.154038759238 , 0.465448988754 , 2.61963693639 ] ]
DataSetDict['01_CBCT_2ndMolar_left'] = [ [ -0.0833104503839 , 0.648108642342 , 0.75697724971 , 11.5249064639 ],
                    [ -0.945423990569 , 0.0540275370771 , 0.321332387559 , 19.1935513512 ],
                    [ -0.559525230311 , -0.701242037349 , 0.44180439303 , -11.5201891223 ],
                    [ 0.543750721411 , -0.74716377883 , 0.38220601849 , -34.7381546073 ],
                    [ 0.960044394802 , -0.27932004746 , -0.0171776336194 , -27.3046851227 ],
                    [ 0.737425629974 , 0.654347209408 , 0.167431089695 , -0.379002006576 ] ]
DataSetDict['01_CBCT_2ndMolar_right'] =  [
                    [ 0.0817980059134 , 0.0758087346348 , 0.993761602187 , -8.02486042162 ],
                    [ 0.0784264719677 , 0.93384113406 , 0.348984275909 , 21.2037103638 ],
                    [ -0.649856411371 , 0.755155625044 , 0.0861778774639 , 3.62588256472 ],
                    [ -0.819540501573 , -0.505895306979 , 0.269115782998 , -32.6332843588 ],
                    [ 0.698721481871 , -0.709187388031 , 0.0940294604351 , -3.61130283564 ],
                    [ 0.85001014928 , 0.0983941593763 , 0.517495251691 , 12.1863476586 ] ]

# Run algorithm on each entry in the dataset dictionary:

# Parameters
simulateFracture = False
# -- Fracture simulation parameters
fractureSize = 0.1
# -- Wavelet analysis parameters
high_sub_bands = 4
levels = 4
# -- Target resolution parameters
targetSpacing = 0.085
# Directory that has all the subdirectories in DataSetDict
dataDirectory = 'Data/'

for directoryName, planeEquations in DataSetDict.iteritems():
    # Set variables for the algorithm
    # Data
    workingDirectory = os.path.join(dataDirectory, directoryName)
    inputImage = 'ToothCBCT.nrrd'
    inputLabelImage = 'ToothCBCT-label.nrrd'
    resampledInput = 'ToothCBCT-resampled.nrrd'
    waveletAnalysisOutputPrefix = 'wavelet'

    print '========== Processing: ' + workingDirectory
    if simulateFracture:
        num = 0

        for planeEquation in planeEquations:
            print "**** Processing fracture number: " + str(num)
            namePostfix = '_'+str(num)
            waveletAnalysisDirectoryName = 'FracturedToothWavelet' + namePostfix
            simulateFractureAndCreateWavelets(workingDirectory, inputImage, inputLabelImage, resampledInput,
                    waveletAnalysisDirectoryName, waveletAnalysisOutputPrefix,
                    True, planeEquation,
                    fractureSize, high_sub_bands, levels, targetSpacing, namePostfix, True)
            num +=1
    else:
        print "***** Processing the resampled input"
        waveletAnalysisDirectoryName = 'NoFractureToothWavelet'
        simulateFractureAndCreateWavelets(workingDirectory, inputImage, inputLabelImage, resampledInput,
                waveletAnalysisDirectoryName, waveletAnalysisOutputPrefix,
                False, [0,0,0,1],
                fractureSize, high_sub_bands, levels, targetSpacing, '',  True)
