#include <itkImageFileReader.h>
#include <itkImageFileWriter.h>
#include <itkImageRegionIteratorWithIndex.h>
#include <itkLabelStatisticsImageFilter.h>
#include <itkThresholdImageFilter.h>
#include <itkAdditiveGaussianNoiseImageFilter.h>
#include <itkClampImageFilter.h>
#include <itkResampleImageFilter.h>
#include <itkNearestNeighborInterpolateImageFunction.h>
#include <itkImageDuplicator.h>
#include <string>

int main(int argc, char* argv[])
{
  if(argc != 11 )
  {
    std::cerr << "Usage: " << argv[0] << "input reference label outputImage outputLabel a b c d displacement" << std::endl;
    std::cerr << "a b c d: plane equation" << std::endl;
    std::cerr << "label: 1=tooth, 2=dark/fracture" << std::endl;
    std::cerr << "Reference image: used to resample output image" << std::endl;
    return 1;
  }
  typedef short PixelType;
  PixelType darkLabel = 2;
  PixelType toothLabel = 1;
  double standardDeviationCorrectionFactor = 5;
  // Parameters
  std::string inputFileName=argv[1];
  std::string referenceFileName=argv[2];
  std::string labelFileName=argv[3];
  std::string outputFileName=argv[4];
  std::string outLabelFileName=argv[5];
  // Plane equation parameters
  double a=std::stod(argv[6]);
  double b=std::stod(argv[7]);
  double c=std::stod(argv[8]);
  double d=std::stod(argv[9]);
  double displacement=std::stod(argv[10]);
  itk::Vector<double,3> normal;
  normal[0]=a;
  normal[1]=b;
  normal[2]=c;
  normal.Normalize();
  std::cout<<"Equation: "<<a<< " " <<b << " "<<c<<" "<<d<<std::endl;
  // read input image
  typedef itk::Image<PixelType,3> InputImageType;
  typedef itk::ImageFileReader<InputImageType> InputReaderType;
  InputReaderType::Pointer reader = InputReaderType::New();
  reader->SetFileName(inputFileName);
  reader->Update();

  // Read reference image used to resample input image (most likely upsample)
  typedef itk::Image<unsigned char,3> ReferenceImageType; // Just used for size, spacing,...
  typedef itk::ImageFileReader<InputImageType> ReferenceReaderType;
  ReferenceReaderType::Pointer referenceReader = ReferenceReaderType::New();
  referenceReader->SetFileName(referenceFileName);
  referenceReader->Update();
  
  typedef itk::ResampleImageFilter<InputImageType,InputImageType> ResampleFilterType;
  ResampleFilterType::Pointer resample = ResampleFilterType::New();
  resample->SetInput(reader->GetOutput());
  resample->SetReferenceImage(referenceReader->GetOutput());
  resample->UseReferenceImageOn();
  resample->Update();
  
  // Copy input image
  typedef itk::ImageDuplicator< InputImageType > DuplicatorType;
  DuplicatorType::Pointer duplicator = DuplicatorType::New();
  duplicator->SetInputImage(resample->GetOutput());
  duplicator->Update();
  InputImageType::Pointer output=duplicator->GetOutput();
  
  // Read label map (region to deform)
  typedef itk::Image<unsigned char,3> LabelImageType;
  typedef itk::ImageFileReader<LabelImageType> LabelReaderType;
  LabelReaderType::Pointer labelReader = LabelReaderType::New();
  labelReader->SetFileName(labelFileName);
  labelReader->Update();

  typedef itk::NearestNeighborInterpolateImageFunction<LabelImageType> NNType;
  NNType::Pointer NN = NNType::New();
  typedef itk::ResampleImageFilter<LabelImageType,LabelImageType> LabelResampleFilterType;
  LabelResampleFilterType::Pointer labelResample = LabelResampleFilterType::New();
  labelResample->SetInput(labelReader->GetOutput());
  labelResample->SetInterpolator(NN);
  labelResample->SetReferenceImage(referenceReader->GetOutput());
  labelResample->UseReferenceImageOn();
  labelResample->Update();
  
  
  // Copy labelmap image
  typedef itk::ImageDuplicator< LabelImageType > LabelDuplicatorType;
  LabelDuplicatorType::Pointer labelDuplicator = LabelDuplicatorType::New();
  labelDuplicator->SetInputImage(labelResample->GetOutput());
  labelDuplicator->Update();
  
  // Compute tooth mask
  LabelImageType::Pointer toothMask;
  typedef itk::ThresholdImageFilter<LabelImageType> ThresholdFilterType;
  ThresholdFilterType::Pointer thresholdFilter = ThresholdFilterType::New();
  thresholdFilter->SetInput(labelResample->GetOutput());
  thresholdFilter->ThresholdOutside(1,1);
  thresholdFilter->Update();
  toothMask = thresholdFilter->GetOutput();
    
  //Generate noise image
  typedef itk::LabelStatisticsImageFilter< InputImageType, LabelImageType > StatisticsFilterType;
  StatisticsFilterType::Pointer statisticsFilter = StatisticsFilterType::New();
  statisticsFilter->SetInput(resample->GetOutput());
  statisticsFilter->SetLabelInput(labelResample->GetOutput());
  statisticsFilter->Update();
  PixelType mean = statisticsFilter->GetMean(darkLabel);
  PixelType std = statisticsFilter->GetSigma(darkLabel);
  // Create empty noise image
  typedef itk::Image<float,3> NoiseImageType;
  NoiseImageType::Pointer noise=NoiseImageType::New();
  noise->SetRegions(resample->GetOutput()->GetLargestPossibleRegion());
  noise->SetSpacing(resample->GetOutput()->GetSpacing());
  noise->SetDirection(resample->GetOutput()->GetDirection());
  noise->SetOrigin(resample->GetOutput()->GetOrigin());
  noise->Allocate(true);
  // Add gaussian noise to empty noise image
  typedef itk::AdditiveGaussianNoiseImageFilter<NoiseImageType,NoiseImageType> NoiseFilterType;
  NoiseFilterType::Pointer noiseFilter = NoiseFilterType::New();
  noiseFilter->SetInput(noise);
  noiseFilter->SetMean(mean);
  noiseFilter->SetStandardDeviation(std/standardDeviationCorrectionFactor);
  noiseFilter->Update();
  typedef itk::ClampImageFilter< NoiseImageType, InputImageType > ClampFilterType;
  ClampFilterType::Pointer clampFilter = ClampFilterType::New();
  clampFilter->SetInput(noiseFilter->GetOutput());
  clampFilter->Update();
  
  
  // Iterate over plan image to generate region of space on one side of the plane
  // This allows to verify the input equation of the plane
  typedef itk::ImageRegionIteratorWithIndex<InputImageType> InputIteratorType;
  typedef itk::ImageRegionIteratorWithIndex<LabelImageType> LabelIteratorType;
  InputIteratorType itout(output,output->GetLargestPossibleRegion());
  InputIteratorType itnoise(clampFilter->GetOutput(),clampFilter->GetOutput()->GetLargestPossibleRegion());
  LabelIteratorType itmask(labelResample->GetOutput(),labelResample->GetOutput()->GetLargestPossibleRegion());

  for(itmask.GoToBegin(), itnoise.GoToBegin(), itout.GoToBegin(); !itout.IsAtEnd(); ++itmask, ++itnoise, ++itout)
  {
    LabelImageType::IndexType index = itout.GetIndex();
    itk::Point<double,3> point;
    output->TransformIndexToPhysicalPoint(index, point);
    // Plane equation is assumed to be in RAS coordinate space (Slicer/VTK)
    // Point coordinates are in LPS (ITK)
    // The plane equation is assumed to be of the form: ax+by+cz-d (See EasyClip extension in 3D Slicer)
    double val = -a*point[0]-b*point[1]+c*point[2]-d;
    if( std::abs(val) < displacement && itmask.Get() == toothLabel)
    {
      itout.Set(itnoise.Get());
      continue;
    }
    itk::Vector<float,3> forwardDisplacement = normal*displacement;
    // Invert displacement field if on "other" side of plane
    if( val < 0)
    {
      forwardDisplacement = -forwardDisplacement;
    }
    point+=forwardDisplacement;
    LabelImageType::IndexType displacedIndex;
    output->TransformPhysicalPointToIndex(point,displacedIndex);
    if(labelResample->GetOutput()->GetPixel(displacedIndex) == toothLabel)
    {
      itout.Set(resample->GetOutput()->GetPixel(index));
      labelDuplicator->GetOutput()->SetPixel(index,toothLabel);
    }
  }
 
  // Write output image 
  typedef itk::ImageFileWriter<InputImageType> WriterType;
  WriterType::Pointer writer = WriterType::New();
  writer->SetInput(output);
  writer->SetFileName(outputFileName);
  writer->Update();
 
  // Write output label map
  typedef itk::ImageFileWriter<LabelImageType> LabelWriterType;
  LabelWriterType::Pointer labelWriter = LabelWriterType::New();
  labelWriter->SetInput(labelDuplicator->GetOutput());
  labelWriter->SetFileName(outLabelFileName);
  labelWriter->Update();
  
  return 0;
}
