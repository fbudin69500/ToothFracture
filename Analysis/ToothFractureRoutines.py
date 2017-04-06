#!/usr/bin/env python
import os
from subprocess import call
import itk

'''
This file contains functions to run tooth fracture simulation and wavelet analysis.
'''


def smoothImage(inputImageFileName, outputImageFileName, smoothnessSigma):
    print 'Smoothing image: ', inputImageFileName, ' with Sigma ', smoothnessSigma
    reader = itk.ImageFileReader.New(FileName=inputImageFileName)
    reader.Update()
    smoothFilter = itk.SmoothingRecursiveGaussianImageFilter.New(reader)
    smoothFilter.SetSigma(smoothnessSigma)

    itk.ImageFileWriter.New(Input=smoothFilter.GetOutput(), FileName= outputImageFileName).Update()

'''
Function to simulate the fractures and create wavelets
------------------
Input parameters:
-----------------
- workingDirectory: path to the case directory
- inputImage: name of the grayscale image in workingDirectory
- inputLabelImage: name of the labelmap image (segmentation of tooth) in working directory
- resampledInput: name of the resampled grayscale image (this will be used when doing wavelet analysis on healthy grayscale)
- waveletAnalysisDirectoryName: name of directory (in workingDirectory) where wavelet analysis results will be stored
- waveletAnalysisOutputPrefix: prefix for wavelet signal output images
- simulateFracture: True if you need to simulate and analyze a fracture
- planeEquation: A 4-tuple representing a plane along which the fracture is simulated
- fractureSize: desired width of the simulated fracture (in mm)
- high_sub_bands: Number of bands for wavelet analysis
- levels: Number of levels for wavelet analysis
- targetSpacing: target resampled resolution (in mm) for the input image. Fractures will be simulated at this resolution.
- namePostfix = '': A postfix to be applied to wavelet directory names
- tamper=False: If True grayscale images are tampered with a little. Right now smoothness is applied
- overwrite = False: If True function will redo fracture simulation and generate respective output.

---------
Outputs:
---------
- If simulateFracture is true: a grayscale image and corresponding label map with the tooth fracture.
- A directory with high_sub_bands*levels wavelet output signal images.


-------------
Dependencies:
-------------
- ITK compiled with python wrapping and virtual environment setup with itk is ideal to have
- ITKTransformTools: git@github.com:fbudin69500/ITKTransformTools.git
- ToothFractureSimulation command line: from repository: clone git@github.com:fbudin69500/ToothFracture.git
- Wavelet analysis script from above repository
- ITKIsotropicWavelets compiled with BUILD_TESTING OFF, and WRAP_PYTHON ON during cmake configuration
- Change paths to the tools inside the function before you run.

'''

def simulateFractureAndCreateWavelets(workingDirectory, inputImage, inputLabelImage, resampledInput,
            waveletAnalysisDirectoryName, waveletAnalysisOutputPrefix,
            simulateFracture, planeEquation,
            fractureSize, high_sub_bands, levels,
            targetSpacing, namePostfix = '', tamper=False, overwrite = False):

    # locations of command line programs and python scripts
    ###### *********** CHANGE THESE ************** ##############
    ITKTransformTool = 'ITKTransformTools-r/ITKTransformTools'
    ToothFractureSimulationCmd = 'ToothFracture/Simulation/ToothFractureSimulation'
    ToothFractureAnalysisScript = 'ToothFracture/Analysis/ITKIsoWavelets.py'

    '''
    Create reference image (empty image, grid) with 0.085 isotropic spacing:
    git clone git@github.com:fbudin69500/ITKTransformTools.git
    '''
    spacingStr = str(targetSpacing)
    emptyImageName = 'grid_'+spacingStr+'_iso.nrrd'

    commandLine = [ITKTransformTool,
                    'size', os.path.join(workingDirectory, inputImage),
                    '-', '--grid', os.path.join(workingDirectory, emptyImageName),
                    '--spacing', spacingStr, spacingStr, spacingStr]
    print commandLine
    call(commandLine)

    inputForWaveletAnalysis = ''
    if simulateFracture:
        # Run fracture simulation
        # git clone git@github.com:fbudin69500/ToothFracture.git

        outputFractureFile = os.path.join(workingDirectory, 'fracturedTooth'+namePostfix+'.nrrd')

        # Run the fracture simulatin
        if overwrite or  not os.path.exists(outputFractureFile):
            print 'Simulating fracture'
            commandLine = [ToothFractureSimulationCmd,
                           os.path.join(workingDirectory, inputImage),
                           os.path.join(workingDirectory, emptyImageName),
                           os.path.join(workingDirectory, inputLabelImage),
                           outputFractureFile,
                           os.path.join(workingDirectory, 'fracturedToothLabel' + namePostfix + '.nrrd'),
                           str(planeEquation[0]), str(planeEquation[1]), str(planeEquation[2]), str(planeEquation[3]),
                           str(fractureSize)]
            print commandLine
            call(commandLine)
        else:
            print "Bypassing simulating fractures since either the file exists and overwrite was not requested"
        inputForWaveletAnalysis = os.path.join(workingDirectory, 'fracturedTooth'+namePostfix+'.nrrd')
    else:
        inputForWaveletAnalysis = os.path.join(workingDirectory, resampledInput)

    if tamper:
        print 'Will tamper with image here'
        tamperedOutputFileName = os.path.join(workingDirectory, 'temp.nrrd')
        smoothImage(inputForWaveletAnalysis, tamperedOutputFileName, 1.5*fractureSize)
        inputForWaveletAnalysis = tamperedOutputFileName

    # Run wavelet analysis
    print "Running wavelet analysis"
    waveletDirectoryPath = os.path.join(workingDirectory, waveletAnalysisDirectoryName)
    if not os.path.exists(waveletDirectoryPath):
        print 'creating directory: ' + waveletDirectoryPath
        os.mkdir(waveletDirectoryPath)

    commandLine = [ToothFractureAnalysisScript,
                  inputForWaveletAnalysis,
                  os.path.join(waveletDirectoryPath, waveletAnalysisOutputPrefix),
                  str(high_sub_bands), str(levels)]
    call(commandLine)

    print('Done!')
