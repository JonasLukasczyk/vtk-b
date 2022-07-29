import bpy
import numpy
from vtk.util.numpy_support import vtk_to_numpy

from ..core import VTKB_Category
from .VTKB_Node import VTKB_Node
from .. import registry


# Print iterations progress
def printProgressBar(
  iteration, total,
  prefix='', suffix='',
  decimals=1, length=100,
  fill='%', printEnd="\r"
):
  """
  Call in a loop to create terminal progress bar
  @params:
      iteration   - Required  : current iteration (Int)
      total       - Required  : total iterations (Int)
      prefix      - Optional  : prefix string (Str)
      suffix      - Optional  : suffix string (Str)
      decimals    - Optional  : positive number of decimals in percent complete (Int)
      length      - Optional  : character length of bar (Int)
      fill        - Optional  : bar fill character (Str)
      printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
  """
  percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
  filledLength = int(length * iteration // total)
  bar = fill * filledLength + '-' * (length - filledLength)
  print(f'\r{prefix} [{bar}] {percent}% {suffix}', end = printEnd)
  # Print New Line on Complete
  if iteration == total:
      print()

def addAttributes(vtkDataObject,blenderObject):
  # add all attributes
  attributeDomain = ['POINT','FACE']
  for a in range(0,2):
    data = vtkDataObject.GetAttributesAsFieldData(a)
    for i in range(data.GetNumberOfArrays()):
      array = data.GetArray(i)
      blenderType = None
      target = None
      if array.GetNumberOfComponents()==1:
        blenderType = 'FLOAT'
        target='value'
      elif array.GetNumberOfComponents()==3:
        blenderType = 'FLOAT_VECTOR'
        target='vector'
      else:
        print('ERROR: Unsupported Data Type:')
        print(array)
      # match array.GetDataType():
      #   case 10:
      #     if array.GetNumberOfComponents()==1:
      #       blenderType = 'FLOAT'
      #       target='value'
      #     elif array.GetNumberOfComponents()==3:
      #       blenderType = 'FLOAT_VECTOR'
      #       target='vector'
      #   case 6:
      #     if array.GetNumberOfComponents()==1:
      #       blenderType = 'INT'
      #       target='value'
      #   case 2:
      #     if array.GetNumberOfComponents()==1:
      #       blenderType = 'INT8'
      #       target='value'
      #   case _:
      #     print('ERROR: Unsupported Data Type:')
      #     print(array)

      if blenderType!=None and target!=None:
        attribute = blenderObject.data.attributes.new(
          name=array.GetName(),
          type=blenderType,
          domain=attributeDomain[a]
        )
        attribute.data.foreach_set(
          target,
          vtk_to_numpy(array).ravel().astype('f4')
        )

  return 1

def addToVTKCollection(blenderObject):
  blenderCollection = bpy.data.collections.get('VTK')
  if not blenderCollection:
    blenderCollection = bpy.data.collections.new('VTK')
    bpy.context.scene.collection.children.link(blenderCollection)
  blenderCollection.objects.link(blenderObject)

  blenderObject.select_set(True)
  bpy.context.view_layer.objects.active = blenderObject

def initBlenderObject(name,blenderMesh):
  blenderObject = bpy.data.objects.get(name)
  if not blenderObject:
    blenderObject = bpy.data.objects.new(name, blenderMesh)
  return blenderObject

def deleteBlenderObject(name):
  toDelete = []
  for obj in bpy.data.objects:
    if obj.name.startswith(name):
      toDelete.append(obj)

  for obj in toDelete:
    bpy.data.objects.remove(obj, do_unlink=True)

  return 1

def initBlenderMesh(name):
  blenderMesh = bpy.data.meshes.get(name)
  materials = []
  if blenderMesh:
    for m in blenderMesh.materials:
      materials.append(m)
    bpy.data.meshes.remove(blenderMesh, do_unlink=True)
  blenderMesh = bpy.data.meshes.new(name)
  for m in materials:
    blenderMesh.materials.append(m)

  return blenderMesh

def vtkOutlineToBlender(vtkDataObject,name):

  bounds = vtkDataObject.GetBounds()

  blenderMesh = initBlenderMesh(name)

  # vertices
  blenderMesh.vertices.add(8)
  blenderMesh.vertices.foreach_set("co", numpy.array([
    bounds[0],bounds[2],bounds[4],
    bounds[1],bounds[2],bounds[4],
    bounds[1],bounds[3],bounds[4],
    bounds[0],bounds[3],bounds[4],
    bounds[0],bounds[2],bounds[5],
    bounds[1],bounds[2],bounds[5],
    bounds[1],bounds[3],bounds[5],
    bounds[0],bounds[3],bounds[5]
  ]))

  cells = 6
  blenderMesh.loops.add(4*cells)
  blenderMesh.loops.foreach_set("vertex_index", numpy.array([
    1,0,3,2,
    4,5,6,7,
    0,1,5,4,
    1,2,6,5,
    2,3,7,6,
    3,0,4,7,
  ]))

  offsetArray = numpy.array([i for i in range(0,4*(cells+1),4)])
  blenderMesh.polygons.add(len(offsetArray)-1)
  blenderMesh.polygons.foreach_set("loop_total", numpy.diff(offsetArray))
  blenderMesh.polygons.foreach_set("loop_start", offsetArray[:-1])

  blenderMesh.update()
  blenderMesh.validate()

  blenderObject = initBlenderObject(name,blenderMesh)
  wireframe = blenderObject.modifiers.new('WIREFRAME', 'WIREFRAME')
  wireframe.offset = 1

  addToVTKCollection(blenderObject)
  return 1

def vtkMeshToBlender(vtkDataObject,name):

  points = vtkDataObject.GetPoints()
  if not points:
    return 0

  cells = None
  if vtkDataObject.IsA('vtkPolyData'):
    cells = vtkDataObject.GetPolys()
    if not cells:
      cells = vtkDataObject.GetLines()
  elif vtkDataObject.IsA('vtkUnstructuredGrid'):
    cells = vtkDataObject.GetCells()
  if not cells:
    return 0

  printProgressBar(0, 6, prefix = 'ToBlender:', suffix = '', length = 50)

  # create new mesh and remember materials
  blenderMesh = initBlenderMesh(name)

  # vertices
  blenderMesh.vertices.add(vtkDataObject.GetNumberOfPoints())
  blenderMesh.vertices.foreach_set("co", vtk_to_numpy(points.GetData()).ravel())

  printProgressBar(1, 6, prefix = 'ToBlender:', suffix = '', length = 50)

  # connectivity
  connectivityArray = vtk_to_numpy(cells.GetConnectivityArray())
  blenderMesh.loops.add(len(connectivityArray))
  blenderMesh.loops.foreach_set("vertex_index", connectivityArray)

  # print('end convert 2')
  printProgressBar(2, 6, prefix = 'ToBlender:', suffix = '', length = 50)
  # offsets
  offsetArray = vtk_to_numpy(cells.GetOffsetsArray())
  blenderMesh.polygons.add(len(offsetArray)-1)
  blenderMesh.polygons.foreach_set("loop_total", numpy.diff(offsetArray))
  blenderMesh.polygons.foreach_set("loop_start", offsetArray[:-1])

  # print('end convert 3')
  printProgressBar(3, 6, prefix = 'ToBlender:', suffix = '', length = 50)

  blenderObject = initBlenderObject(name,blenderMesh)
  # delete all attributes
  for attribute in blenderObject.data.attributes:
    blenderObject.data.attributes.remove(attribute, do_unlink=True)

  addAttributes(vtkDataObject,blenderObject)

  printProgressBar(4, 6, prefix = 'ToBlender:', suffix = '', length = 50)
  blenderMesh.update()
  printProgressBar(5, 6, prefix = 'ToBlender:', suffix = '', length = 50)
  blenderMesh.validate()

  addToVTKCollection(blenderObject)

  printProgressBar(6, 6, prefix = 'ToBlender:', suffix = '', length = 50)
  return 1

def convertVtkDataObject(vtkDataObject,socket,name):

  if vtkDataObject.IsA('vtkMultiBlockDataSet'):
    for b in range(vtkDataObject.GetNumberOfBlocks()):
      convertVtkDataObject(vtkDataObject.GetBlock(b),socket,name+'_B'+str(b))
    return 1

  if socket.modifiedTime == vtkDataObject.GetMTime() and bpy.data.objects.get(name):
    return 1
  socket.modifiedTime = vtkDataObject.GetMTime()

  if vtkDataObject.IsA('vtkImageData'):
    print('unable to convert vtkImageData yet')
  else:
    return vtkMeshToBlender(vtkDataObject,name)
  return 0

def convertVtkDataObjectFromSocket(socket):
  if socket.bl_idname != 'VTKB_NodeSocketDataObject':
    return 0

  node = socket.node
  name = node.name
  if len(node.outputs)>1:
    name += '_'+str(socket.index)

  if not socket.convert:
    deleteBlenderObject(name+'_M')
  if not socket.outline:
    deleteBlenderObject(name+'_BB')
  if not socket.convert and not socket.outline:
    return 1

  vtkAlgorithm,_ = node.getVtkAlgorithm()
  if not vtkAlgorithm:
    return 0

  vtkDataObject = vtkAlgorithm.GetOutputDataObject(socket.index)
  if not vtkDataObject:
    return 0

  if socket.outline:
    vtkOutlineToBlender(vtkDataObject,name+'_BB')
  if socket.convert:
    return convertVtkDataObject(vtkDataObject,socket,name+'_M')

  return 1

################################################################################
class VTKB_NodeConverters(VTKB_Node):
  bl_idname= 'VTKB_NodeConverters'

class VTKB_ToBlenderMesh(VTKB_NodeConverters):

  bl_idname= 'VTKB_ToBlenderMesh'
  bl_label = 'Blender Mesh'

  def init(self,context):
    s = self.inputs.new('VTKB_NodeSocketDataObject', 'vtkDataObject')

  def draw_buttons(self,context,layout):
    row = layout.row(align=True)

  def convert(self):
    if self.mute:
      return

    links = self.inputs['vtkDataObject'].links
    if len(links)!=1:
      return

    self.setStatus('out-of-date')
    status = convertVtkDataObject(links[0].from_socket)
    if status:
      self.setStatus('up-to-date')
    else:
      self.setStatus('error')

VTKB_Category.VTKB_Category.addItem('Blender',VTKB_ToBlenderMesh)
registry.UI_CLASSES.append(VTKB_ToBlenderMesh)
