import requests
import xml.etree.ElementTree as ET

from ..core import VTKB_Category
from .VTKB_NodeAlgorithm import VTKB_NodeAlgorithm

import vtk
import topologytoolkit as ttk

EXPORTS = []

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
    print("ERROR")
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

        # enums = proxy.findall('.//EnumerationDomain')
        # if enums:
        #   return ('VTKB_NodeSocketEnum',name,method,default_values)
        # else:
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
        value[i] = int(value[i])

    return ('VTKB_NodeSocketArray',name,method,value)
  else:
    print('ERROR')
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
  vtkAlgorithm = None
  if classname.startswith('vtk'):
    vtkAlgorithm = getattr(vtk, classname, None)
  elif classname.startswith('ttk'):
    vtkAlgorithm = getattr(ttk, classname, None)

  if not vtkAlgorithm:
    print("ERROR")
    return None

  o = vtkAlgorithm()

  members = {
    'bl_idname': vtkAlgorithm.__name__,
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

def generateVTKBNodesFromXMLS():
  xml_urls = [
    "https://gitlab.kitware.com/paraview/paraview/-/raw/master/Remoting/Application/Resources/filters_filterscore.xml",
    "https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/CinemaReader.xml",
    "https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/CinemaQuery.xml",
    "https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/CinemaProductReader.xml",
    "https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/Icosphere.xml",
    "https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/HelloWorld.xml",
    "https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/Identifiers.xml",
    "https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/Extract.xml",
    'https://raw.githubusercontent.com/JonasLukasczyk/ttk/trackingAPI3/paraview/xmls/MergeTree.xml'
  ]

  for url in xml_urls:
    response = requests.get(url)
    root = ET.fromstring(response.content)
    proxies = root.findall('.//SourceProxy')
    for proxy in proxies:
      nodeClass = createNodeClassFromProxy(proxy)
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
        EXPORTS.append(nodeClass)

def export():
  return EXPORTS

