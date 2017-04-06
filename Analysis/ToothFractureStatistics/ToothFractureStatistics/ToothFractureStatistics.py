import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import csv

INPUT_DIR = os.path.dirname(os.path.realpath(__file__)) + '/../../Data'


#
# ToothFractureStatistics
#

class ToothFractureStatistics(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = "ToothFractureStatistics"  # TODO make this more human readable by adding spaces
        self.parent.categories = ["Tooth Fracture"]
        self.parent.dependencies = []
        self.parent.contributors = ["Hina Shah (Kitware Inc)"]  # replace with "Firstname Lastname (Organization)"
        self.parent.helpText = """
      Extension to qunatify the automatic detection of tooth fracture in CBCT using wavelets.
      """
        self.parent.helpText += self.getDefaultModuleDocumentationLink()
        self.parent.acknowledgementText = """
        This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
        and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
        s"""  # replace with organization, grant and thanks.


#
# ToothFractureStatisticsWidget
#

class ToothFractureStatisticsWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # Instantiate and connect widgets ...

        #
        # Parameters Area
        #
        parametersCollapsibleButton = ctk.ctkCollapsibleButton()
        parametersCollapsibleButton.text = "Parameters"
        self.layout.addWidget(parametersCollapsibleButton)

        # Layout within the dummy collapsible button
        parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

        # input directory selector
        self.InputDirectorySelector = ctk.ctkDirectoryButton()
        self.InputDirectorySelector.caption = 'Input Data Directory'
        self.InputDirectorySelector.directory = INPUT_DIR
        self.UpdateDirectoryButtonText(self.InputDirectorySelector)
        self.InputDirectorySelector.connect('directoryChanged(QString)', self.onInputDirectoryChanged)
        parametersFormLayout.addRow("Data Directory", self.InputDirectorySelector)

        # Output file name
        self.outputFileName = qt.QLineEdit("ToothFractureWaveletStatistics.csv")
        parametersFormLayout.addRow("Output File Name", self.outputFileName)

        #
        # threshold value
        #
        self.imageThresholdSliderWidget = ctk.ctkSliderWidget()
        self.imageThresholdSliderWidget.singleStep = 1.0
        self.imageThresholdSliderWidget.minimum = 0
        self.imageThresholdSliderWidget.maximum = 100
        self.imageThresholdSliderWidget.value = 95
        self.imageThresholdSliderWidget.setToolTip(
            "Set the percentile value to record if Use Percentile checkbox is checked.")
        parametersFormLayout.addRow("Precentile", self.imageThresholdSliderWidget)

        #
        # check box to trigger taking screen shots for later use in tutorials
        #
        self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
        self.enableScreenshotsFlagCheckBox.checked = 0
        self.enableScreenshotsFlagCheckBox.setToolTip(
            "If checked, use n'th percentile value (chosen from above slider) as the feature value, else just the max.")
        parametersFormLayout.addRow("Use Percentile", self.enableScreenshotsFlagCheckBox)

        #
        # Apply Button
        #
        self.applyButton = qt.QPushButton("Apply")
        self.applyButton.toolTip = "Run the algorithm."
        self.applyButton.enabled = False
        parametersFormLayout.addRow(self.applyButton)

        # connections
        self.applyButton.connect('clicked(bool)', self.onApplyButton)

        # Add vertical spacer
        self.layout.addStretch(1)

        # Refresh Apply button state
        self.onSelect()

    def cleanup(self):
        pass

    def onSelect(self):
        self.applyButton.enabled = True  # self.inputSelector.currentNode() and self.outputSelector.currentNode()

    def onApplyButton(self):
        logic = ToothFractureStatisticsLogic()
        usePercentiles = self.enableScreenshotsFlagCheckBox.checked
        percentileValue = self.imageThresholdSliderWidget.value
        outputFileName = self.outputFileName.text
        logic.run(self.InputDirectorySelector.directory, outputFileName, percentileValue, usePercentiles)

    def UpdateDirectoryButtonText(self, directory_button, length=40):
        dir_str = directory_button.directory
        dir_length = len(dir_str)
        if dir_length <= length or length < 4:
            directory_button.text = dir_str
        else:
            part_length = int(round(length / 2.0))
            left_dir_str = dir_str[:part_length - 1]
            right_dir_str = dir_str[-part_length + 1:]
            directory_button.text = left_dir_str + '...' + right_dir_str

    def onInputDirectoryChanged(self):
        self.UpdateDirectoryButtonText(self.InputDirectorySelector)


#
# ToothFractureStatisticsLogic
#

class ToothFractureStatisticsLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python  computation done by your module.  The interface
/slicer/ScriptedLoadableModule.py
  """

    def hasImageData(self, volumeNode):
        """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
        if not volumeNode:
            logging.debug('hasImageData failed: no volume node')
            return False
        if volumeNode.GetImageData() is None:
            logging.debug('hasImageData failed: no image data in volume node')
            return False
        return True

    def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
        """Validates if the output is not the same as input
    """
        if not inputVolumeNode:
            logging.debug('isValidInputOutputData failed: no input volume node defined')
            return False
        if not outputVolumeNode:
            logging.debug('isValidInputOutputData failed: no output volume node defined')
            return False
        if inputVolumeNode.GetID() == outputVolumeNode.GetID():
            logging.debug(
                'isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
            return False
        return True

    def takeScreenshot(self, name, description, type=-1):
        # show the message even if not taking a screen shot
        slicer.util.delayDisplay(
            'Take screenshot: ' + description + '.\nResult is available in the Annotations module.', 3000)

        lm = slicer.app.layoutManager()
        # switch on the type to get the requested window
        widget = 0
        if type == slicer.qMRMLScreenShotDialog.FullLayout:
            # full layout
            widget = lm.viewport()
        elif type == slicer.qMRMLScreenShotDialog.ThreeD:
            # just the 3D window
            widget = lm.threeDWidget(0).threeDView()
        elif type == slicer.qMRMLScreenShotDialog.Red:
            # red slice window
            widget = lm.sliceWidget("Red")
        elif type == slicer.qMRMLScreenShotDialog.Yellow:
            # yellow slice window
            widget = lm.sliceWidget("Yellow")
        elif type == slicer.qMRMLScreenShotDialog.Green:
            # green slice window
            widget = lm.sliceWidget("Green")
        else:
            # default to using the full window
            widget = slicer.util.mainWindow()
            # reset the type so that the node is set correctly
            type = slicer.qMRMLScreenShotDialog.FullLayout

        # grab and convert to vtk image data
        qpixMap = qt.QPixmap().grabWidget(widget)
        qimage = qpixMap.toImage()
        imageData = vtk.vtkImageData()
        slicer.qMRMLUtils().qImageToVtkImageData(qimage, imageData)

        annotationLogic = slicer.modules.annotations.logic()
        annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

    def loadMRMLNode(self, node_name, file_dir, file_name, file_type):
        node = slicer.util.getNode(node_name)
        if node is None:
            properties = {}
            file_path = os.path.join(file_dir, file_name)
            if file_type == 'LabelMap':
                file_type = 'VolumeFile'
                properties['labelmap'] = True
            node = slicer.util.loadNodeFromFile(file_path, file_type, properties, returnNode=True)
            node = node[1]
            if node is None:
                logging.error('!!! Failed to load: %s', file_path)
                return -1
            if file_type == 'MarkupsFiducials':
                node.SetLocked(1)
            node.SetName(node_name)
        return node

    def processCase(self, path, waveletDirectory, waveletRange, classification, csvWriter):
        fullpath = os.path.join(path, waveletDirectory)
        caseName = os.path.split(path)[1]
        row = [caseName, waveletDirectory, classification]
        pad = 20  # This is used to counter the wavelet property/bug which somehow has an interpolation of the original image
        for waveletNumber in waveletRange:
            nodeName = 'wavelet' + str(waveletNumber)
            imagename = nodeName + '.nrrd'
            waveletImage = self.loadMRMLNode(nodeName, fullpath, imagename, 'VolumeFile')
            if waveletImage is not None:
                waveletArray = abs(slicer.util.array(nodeName))
                imageShape = waveletArray.shape
                subimage = waveletArray[pad - 1:imageShape[0] - pad - 1, pad - 1:imageShape[1] - pad - 1,
                           pad - 1:imageShape[2] - pad - 1]
                if self.usePercentiles:
                    import numpy
                    maxValue = numpy.percentile(subimage, self.percentileValue)
                else:
                    maxValue = subimage.max()

                # report max
                print 'image: ' + caseName + ' ' + waveletDirectory + ' ' + nodeName
                print maxValue
                # create the row for csv file:
                row.append(str(maxValue))
                # cleanup
                slicer.mrmlScene.RemoveNode(waveletImage)
        csvWriter.writerow(row)

    def run(self, inputDataDirectory, outputFileName, percentileValue, usePercentiles=False, enableScreenshots=0):
        """
    Run the actual algorithm
    """
        # Find the first level directories in the input Directory which has directories by the names of
        # FracturedToothWavelet_0 and NoFractureToothWavelet
        paths = []
        for dirpath, dirnames, filenames in os.walk(inputDataDirectory):
            if 'FracturedToothWavelet_0' in dirnames and 'NoFractureToothWavelet' in dirnames:
                paths.append(dirpath)

        # paths now has all the cases
        # Create a list of directories to process:
        waveletDirectories = ['NoFractureToothWavelet']
        for i in range(0, 6):
            waveletDirectories.append('FracturedToothWavelet_' + str(i))

        waveletRange = range(0, 16)

        # Create a csv file
        csvFilePath = os.path.join(inputDataDirectory, outputFileName)
        csvFile = open(csvFilePath, 'w')
        cw = csv.writer(csvFile, delimiter=',')

        headerRow = ['Case Name', 'FractureNumber', 'Classification']
        for rangeNum in waveletRange:
            headerRow.append('wavelet' + str(rangeNum))
        cw.writerow(headerRow)

        self.usePercentiles = usePercentiles
        self.percentileValue = percentileValue

        # Process all the wavelet directories
        for path in paths:
            for waveletDirectory in waveletDirectories:
                className = 'NotFractured' if waveletDirectory is 'NoFractureToothWavelet' else 'Fractured'
                self.processCase(path, waveletDirectory, waveletRange, className, cw)

        # Capture screenshot
        if enableScreenshots:
            self.takeScreenshot('ToothFractureStatisticsTest-Start', 'MyScreenshot', -1)

        csvFile.close()

        logging.info('Processing completed')

        return True


class ToothFractureStatisticsTest(ScriptedLoadableModuleTest):
    """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

    def setUp(self):
        """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
        slicer.mrmlScene.Clear(0)

    def runTest(self):
        """Run as few or as many tests as needed here.
    """
        self.setUp()
        self.test_ToothFractureStatistics1()

    def test_ToothFractureStatistics1(self):
        """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

        self.delayDisplay("Starting the test")
        #
        # first, get some data
        #
        import urllib
        downloads = (
            ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

        for url, name, loader in downloads:
            filePath = slicer.app.temporaryPath + '/' + name
            if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
                logging.info('Requesting download %s from %s...\n' % (name, url))
                urllib.urlretrieve(url, filePath)
            if loader:
                logging.info('Loading %s...' % (name,))
                loader(filePath)
        self.delayDisplay('Finished with download and loading')

        volumeNode = slicer.util.getNode(pattern="FA")
        logic = ToothFractureStatisticsLogic()
        self.assertIsNotNone(logic.hasImageData(volumeNode))
        self.delayDisplay('Test passed!')
