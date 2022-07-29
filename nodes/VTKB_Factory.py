import requests
import xml.etree.ElementTree as ET
import hashlib

from ..core import VTKB_Category
from .VTKB_NodeAlgorithm import VTKB_NodeAlgorithm
from .. import registry


import vtk
import topologytoolkit as ttk

def getAttribute(node,attribute):
  try:
    return node.attrib[attribute]
  except KeyError:
    return None

class PropertyTemplateObject():
  def __init__(self,type,name,method,defaultValue,extras={}):
    self.type = type
    self.name = name
    self.method = method
    self.value = defaultValue
    self.extras = extras

  def copy(self):
    return PropertyTemplateObject(self.type,self.name,self.method,self.value)

def createPropertyTemplateFromProxy(proxy):

  name = getAttribute(proxy,'label')
  if not name:
    name = getAttribute(proxy,'name')
  if not name:
    print("[VTK-B][ERROR] Unable to retrieve property name:",proxy)
    return None
  method = getAttribute(proxy,'command')

  nElements = getAttribute(proxy,'number_of_elements')
  if not nElements:
    nElements=1
  else:
    nElements = int(nElements)

  default_values = getAttribute(proxy,'default_values')

  if nElements==3:
    if not default_values:
      default_values = '0 0 0'
    return ('NodeSocketVector',name,method,[float(i) for i in default_values.split()])
  elif nElements==1:
    match proxy.tag:
      case 'IntVectorProperty':
        if not default_values:
          default_values = 0
        else:
          default_values = int(default_values)

        enumerationDomain = proxy.findall('.//EnumerationDomain')
        if len(enumerationDomain)==1:
          enumItems = []
          for enum in enumerationDomain[0].findall('.//Entry'):
            enumItems.append((int(getAttribute(enum,'value')),getAttribute(enum,'text')))
          return ('VTKB_NodeSocketEnum',name,method,default_values,{'enumItems':enumItems})
        else:
          if proxy.findall('.//BooleanDomain'):
            return ('NodeSocketBool',name,method,bool(default_values))
          else:
            return ('NodeSocketInt',name,method,default_values)
      case 'DoubleVectorProperty':
        if not default_values:
          default_values = 0
        return ('NodeSocketFloat',name,method,float(default_values))
      case 'StringVectorProperty':
        if not default_values:
          default_values = ''
        return ('NodeSocketString',name,method,default_values)
  elif method=='SetInputArrayToProcess':
    value = [0,0,0,0,'']
    if default_values:
      default_values = default_values.split()
      for i in range(len(default_values)):
        value[i] = default_values[i]
      for i in range(4):
        if type(value[i]) != int and value[i].isnumeric():
          value[i] = int(value[i])
        else:
          value[i] = 0

    return ('VTKB_NodeSocketArray',name,method,value)
  # elif nElements==0:
  else:
    print(
      '[VTK-B][ERROR] Unable to create socket for property:',
      '_'.join([name,method,str(nElements)])
    )
    return None


def createPropertyTemplatesFromProxies(proxies):
  templates = []
  for proxy in proxies:
    template = createPropertyTemplateFromProxy(proxy)
    if template:
      templates.append( PropertyTemplateObject(*template) )
  return templates


def createNodeClassFromProxy(proxy):
  classname = getAttribute(proxy,'class')

  if not classname:
    print("[VTK-B][ERROR] Classname not found: ",proxy)
    return None
  vtkAlgorithm = None
  if classname.startswith('vtk'):
    vtkAlgorithm = getattr(vtk, classname, None)
  elif classname.startswith('ttk'):
    vtkAlgorithm = getattr(ttk, classname, None)

  if not vtkAlgorithm:
    print("[VTK-B][ERROR] Class not found: ",classname)
    return None

  o = vtkAlgorithm()

  # It is possible that several proxies use the same vtkClass, so the classname can not be used as bl_idname.
  # Thus the bl_idname is a combination of the classname and the hash of the proxy
  members = {
    'bl_idname': (vtkAlgorithm.__name__ + str(int(hashlib.md5(ET.tostring(proxy, encoding='utf-8')).hexdigest(), 16)))[:32],
    'bl_label': vtkAlgorithm.__name__,
    'inputTemplates': [],
    'outputTemplates': []
  }

  o = vtkAlgorithm()
  for i in range(0,o.GetNumberOfInputPorts()):
    info = o.GetInputPortInformation(i)
    dt = info.Get(vtk.vtkAlgorithm.INPUT_REQUIRED_DATA_TYPE())
    members['inputTemplates'].append(
      PropertyTemplateObject('VTKB_NodeSocketDataObject',dt,None,i)
    )

  for p in ['IntVectorProperty','DoubleVectorProperty','StringVectorProperty']:
    members['inputTemplates'] += createPropertyTemplatesFromProxies( proxy.findall('.//'+p) )

  if classname.startswith('ttk'):
    members['inputTemplates'].append(PropertyTemplateObject('NodeSocketInt','Debug Level','SetDebugLevel',3))
    members['inputTemplates'].append(PropertyTemplateObject('NodeSocketBool','Use All Cores','SetUseAllCores',True))

  for i in range(0,o.GetNumberOfOutputPorts()):
    info = o.GetOutputPortInformation(i)
    dt = info.Get(vtk.vtkDataObject.DATA_TYPE_NAME())
    if not dt:
      dt = o.GetInputPortInformation(
        info.Get(ttk.ttkAlgorithm.SAME_DATA_TYPE_AS_INPUT_PORT())
      ).Get(vtk.vtkAlgorithm.INPUT_REQUIRED_DATA_TYPE())
    if not dt:
      dt = 'output-'+str(i)
    members['outputTemplates'].append(PropertyTemplateObject('VTKB_NodeSocketDataObject',dt,None,i))

  return type( vtkAlgorithm.__name__, (VTKB_NodeAlgorithm,), members )

CUSTOM_XMLS = [
  '''
  <xml><SourceProxy class="vtkXMLGenericDataObjectReader">
    <StringVectorProperty name="Path" command="SetFileName"></StringVectorProperty>
    <Hints>
      <ShowInMenu category="Readers" />
    </Hints>
  </SourceProxy></xml>
  ''',
  '''
  <xml><SourceProxy class="vtkClipDataSet">
    <StringVectorProperty command="SetInputArrayToProcess" name="Scalars" number_of_elements="5"></StringVectorProperty>
    <IntVectorProperty command="SetInsideOut" default_values="0" name="InsideOut" number_of_elements="1">
      <BooleanDomain name="bool" />
    </IntVectorProperty>
    <DoubleVectorProperty command="SetValue" default_values="0" name="Scalar" number_of_elements="1"></DoubleVectorProperty>
    <Hints>
      <ShowInMenu category="Common" />
    </Hints>
  </SourceProxy></xml>
  ''',
  '''
  <xml><SourceProxy class="vtkThreshold">
    <StringVectorProperty command="SetInputArrayToProcess" name="Scalars" number_of_elements="5"></StringVectorProperty>
    <IntVectorProperty command="SetThresholdFunction" default_values="0" name="Mode" number_of_elements="1">
      <EnumerationDomain name="enum">
        <Entry text="Between" value="0" />
        <Entry text="Smaller" value="1" />
        <Entry text="Larger" value="2" />
      </EnumerationDomain>
    </IntVectorProperty>
    <IntVectorProperty command="SetAllScalars" default_values="1" name="All Scalars" number_of_elements="1">
      <BooleanDomain name="bool" />
    </IntVectorProperty>
    <DoubleVectorProperty command="SetLowerThreshold" default_values="0" name="Lower Threshold" number_of_elements="1"></DoubleVectorProperty>
    <DoubleVectorProperty command="SetUpperThreshold" default_values="0" name="Upper Threshold" number_of_elements="1"></DoubleVectorProperty>
    <Hints>
      <ShowInMenu category="Common" />
    </Hints>
  </SourceProxy></xml>
  ''',
]

def generateVTKBNodesFromXML(xml):
  proxies = xml.findall('.//SourceProxy')

  for proxy in proxies:
    nodeClass = createNodeClassFromProxy(proxy)
    if not nodeClass:
      continue
    hints = proxy.findall('Hints')
    cat = None
    if len(hints)==1:
      menu = hints[0].findall('ShowInMenu')
      if len(menu)==1:
        cat = getAttribute(menu[0],'category')
    if cat:
      VTKB_Category.VTKB_Category.addItem(cat.replace(' ',''),nodeClass)
    else:
      VTKB_Category.VTKB_Category.addItem('VTK',nodeClass)

    if nodeClass:
      registry.UI_CLASSES.append(nodeClass)

def generateVTKBNodesFromXMLS():
  xml_urls = [
    "https://gitlab.kitware.com/paraview/paraview/-/raw/master/Remoting/Application/Resources/filters_filterscore.xml",
    "https://gitlab.kitware.com/paraview/paraview/-/raw/master/Remoting/Application/Resources/filters_filtersgeometry.xml",
    "https://gitlab.kitware.com/paraview/paraview/-/raw/master/Remoting/Application/Resources/filters_filtersgeneral.xml",
    # "https://gitlab.kitware.com/paraview/paraview/-/raw/master/Remoting/Application/Resources/filters_filtersgeneric.xml",
    "https://gitlab.kitware.com/paraview/paraview/-/raw/master/Remoting/Application/Resources/filters_filtersflowpaths.xml",

    "https://raw.githubusercontent.com/Kitware/ParaView/master/Plugins/AcceleratedAlgorithms/AcceleratedAlgorithms.xml",

    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ArrayEditor.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ArrayPreconditioning.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/BarycentricSubdivision.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/BlockAggregator.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/BottleneckDistance.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/BranchDecomposition.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/CinemaDarkroom.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/CinemaImaging.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/CinemaProductReader.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/CinemaQuery.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/CinemaReader.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/CinemaWriter.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ComparingSimilarityMatrices.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ComponentSize.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ConnectedComponents.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ContinuousScatterPlot.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ContourAroundPoint.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ContourForests.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ContourTreeAlignment.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/DataSetInterpolator.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/DataSetToTable.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/DepthImageBasedGeometryApproximation.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/DimensionReduction.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/DiscreteGradient.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/DistanceField.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/EigenField.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/EndFor.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/Extract.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/FeatureCorrespondences.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/FiberSurface.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/Fiber.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/FlattenMultiBlock.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ForEach.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/FTMTree.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/FTRGraph.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/GaussianModeClustering.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/GaussianPointCloud.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/GeometrySmoother.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/GhostCellPreconditioning.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/GridLayout.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/HarmonicField.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/HelloWorld.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/IcosphereFromObject.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/IcospheresFromPoints.xml',
    'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/Icosphere.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/IdentifierRandomizer.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/Identifiers.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/IdentifyByScalarField.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ImportEmbeddingFromTable.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/InputPointAdvection.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/IntegralLines.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/JacobiSet.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/LDistanceMatrix.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/LDistance.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MandatoryCriticalPoints.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ManifoldCheck.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MapData.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MatrixToHeatMap.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MergeBlockTables.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MergeTreeClustering.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MergeTreeDistanceMatrix.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MergeTreeRefinement.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MergeTreeTemporalReductionDecoding.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MergeTreeTemporalReductionEncoding.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MergeTree.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MeshGraph.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MeshSubdivision.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MetricDistortion.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MorphologicalOperators.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MorseSmaleComplex.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MorseSmaleQuadrangulation.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/OBJWriter.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/OFFReader.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/OFFWriter.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PerlinNoise.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PersistenceCurve.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PersistenceDiagramApproximation.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PersistenceDiagramClustering.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PersistenceDiagramDistanceMatrix.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PersistenceDiagram.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PersistentGenerators.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PlanarGraphLayout.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PointAdvection.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PointDataConverter.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PointDataSelector.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PointMerger.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PointSetToCurve.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/PointSetToSurface.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ProjectionFromField.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ProjectionFromTable.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/QuadrangulationSubdivision.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/RangePolygon.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ReebSpace.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/RipsComplex.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ScalarFieldCriticalPoints.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ScalarFieldFromPoints.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ScalarFieldNormalizer.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/ScalarFieldSmoother.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/SimilarityAlgorithm.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/SimilarityByDistance.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/SimilarityByGradient.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/SimilarityById.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/SimilarityByJacobiSet.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/SimilarityByMergeTreeSegmentation.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/SimilarityByOverlap.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/SimilarityByPersistencePairs.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/SimilarityMatrixTemporalDownsampling.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/SphereFromPoint.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/StableManifoldPersistence.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/StringArrayConverter.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/SurfaceGeometrySmoother.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TableDataSelector.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TableDistanceMatrix.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TextureMapFromField.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TopologicalCompressionReader.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TopologicalCompressionWriter.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TopologicalCompression.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TopologicalSimplificationByPersistence.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TopologicalSimplification.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TrackingFromFields.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TrackingFromOverlap.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TrackingFromPersistenceDiagrams.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TrackingGraph.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TriangulationManager.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TriangulationReader.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TriangulationRequest.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/TriangulationWriter.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/UncertainDataEstimator.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/WebSocketIO.xml',
    # 'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/WRLExporter.xml',
  ]

  # remote xmls
  for url in xml_urls:
    response = requests.get(url)
    generateVTKBNodesFromXML(ET.fromstring(response.content))

  # custom xmls
  for xml in CUSTOM_XMLS:
    generateVTKBNodesFromXML(ET.fromstring(xml))
