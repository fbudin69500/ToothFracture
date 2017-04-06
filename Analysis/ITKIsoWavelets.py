#!/usr/bin/env python
import itk, sys
from itk import IsotropicWavelets

if len(sys.argv) != 5:
    print "Usage: " + sys.argv[0] + " inputImage outputImage High_sub_bands levels"
    sys.exit(1)
print ("Generating Wavelet Space for input image %s" % sys.argv[1])
inputImage = sys.argv[1]
outputImage = sys.argv[2]
high_sub_bands = int(sys.argv[3])
levels = int(sys.argv[4])

print "Reading image"
reader = itk.ImageFileReader.New(FileName=inputImage)
reader.Update()
spacing = reader.GetOutput().GetSpacing()
origin = reader.GetOutput().GetOrigin()
direction = reader.GetOutput().GetDirection()
castFilter = itk.CastImageFilter[itk.output(reader),itk.Image[itk.F,3]].New(reader)

print "Perform FFT on input image"
fftFilter = itk.ForwardFFTImageFilter.New(castFilter)
fftFilter.Update()
ComplexType=itk.output(fftFilter.GetOutput())
RealImageType = itk.Image[itk.F,3]
inverseFFT = itk.InverseFFTImageFilter[ ComplexType, RealImageType].New()
print "Create Forward Filter Bank"
PointType=itk.Point[itk.D,3]
SimoncelliType = itk.SimoncelliIsotropicWavelet[itk.F,3,PointType]
forwardFilterBankType = itk.WaveletFrequencyFilterBankGenerator[ComplexType,SimoncelliType]
forwardFilterBank = forwardFilterBankType.New()
forwardFilterBank.SetHighPassSubBands( high_sub_bands )
forwardFilterBank.SetSize( fftFilter.GetOutput().GetLargestPossibleRegion().GetSize() )
forwardFilterBank.Update()
print  "Store wavelet filter bank."
for band in range(0,high_sub_bands):
    inverseFFT.SetInput( forwardFilterBank.GetOutput( band ) )
    itk.ImageFileWriter.New(Input=inverseFFT.GetOutput(), FileName=outputImage+str(band)+"FilterBank.nrrd").Update()

wavelet = itk.WaveletFrequencyForward[ComplexType,ComplexType, forwardFilterBankType].New()
wavelet.SetHighPassSubBands(high_sub_bands)
wavelet.SetLevels( levels )
wavelet.SetInput(fftFilter.GetOutput())
wavelet.Update()

for level in range(0, levels):
    for band in range(0,high_sub_bands):
        nOutput = level * wavelet.GetHighPassSubBands() + band;
        print "OutputIndex : " + str(nOutput)
        print "Level: " + str(level + 1) + " / " +str(wavelet.GetLevels())
        print "Band: " + str(band + 1) + " / " + str(wavelet.GetHighPassSubBands())
        print "Largest Region: " + str(wavelet.GetOutput( nOutput ).GetLargestPossibleRegion())
        print "Origin: " + str(wavelet.GetOutput( nOutput ).GetOrigin())
        print "Spacing: " + str(wavelet.GetOutput( nOutput ).GetSpacing())

        inverseFFT.SetInput( wavelet.GetOutput( nOutput ) )
        image = inverseFFT.Update()
        image = inverseFFT.GetOutput()
        image.SetSpacing(spacing*(2**level))
        image.SetDirection(direction)
        image.SetOrigin(origin)
        itk.ImageFileWriter.New(Input=image, FileName=outputImage+str(nOutput)+".nrrd").Update()

approxIndex = int(wavelet.GetTotalOutputs() - 1)
inverseFFT.SetInput( wavelet.GetOutput(approxIndex) )
inverseFFT.Update()
image=inverseFFT.GetOutput()
image.SetSpacing(spacing*(2**levels))
image.SetDirection(direction)
image.SetOrigin(origin)
itk.ImageFileWriter.New(Input=image, FileName=outputImage+str(approxIndex)+".nrrd").Update()
