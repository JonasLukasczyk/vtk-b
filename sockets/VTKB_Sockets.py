import bpy

from ..nodes import VTKB_NodeConverters

EXPORTS = []

################################################################################
class VTKB_NodeSocketDataObject(bpy.types.NodeSocket):
  bl_idname = "VTKB_NodeSocketDataObject"
  bl_label = "Data Object Socket"

  index: bpy.props.IntProperty(default=0)
  modifiedTime: bpy.props.IntProperty(default=-1)
  outline: bpy.props.BoolProperty(default=False, update= lambda socket,_: socket.node.id_data.update())
  convert: bpy.props.BoolProperty(default=False, update= lambda socket,_: socket.node.id_data.update())

  def draw(self, context, layout, node, text):
    if self.is_output:
      layout.label(text=text)
      layout.prop(self,'outline',icon='MESH_CUBE',toggle=True,icon_only=True)
      layout.prop(self,'convert',icon='MESH_ICOSPHERE',toggle=True,icon_only=True)
    else:
      layout.label(text=text)

  def draw_color(self, context, node):
    return (0, 163/255, 225/255, 1)

EXPORTS.append(VTKB_NodeSocketDataObject)

################################################################################
class VTKB_NodeSocketArray(bpy.types.NodeSocket):
  bl_idname = "VTKB_NodeSocketArray"
  bl_label = "Array Socket"

  pIdx: bpy.props.IntProperty(name='Idx',default=0)
  pPort: bpy.props.IntProperty(name='Port',default=0)
  pConnection: bpy.props.IntProperty(name='Connection',default=0)
  pAttribute: bpy.props.IntProperty(name='Attribute',default=0)
  pName: bpy.props.StringProperty(name='Name',default='None')

  def getArrayEnums(self,context):
    items = [("None", "None", "None", 'ERROR', 0)]

    a,p = self.node.getVtkAlgorithm()
    o = a.GetInputDataObject(
      self.pPort,
      self.pConnection
    )
    if not o:
      return items

    icons = ['VERTEXSEL', 'FACESEL', 'MESH_CUBE']
    for attributeIdx in range(0,3):
      data = o.GetAttributesAsFieldData(attributeIdx)
      if not data:
        continue
      for arrayIdx in range(data.GetNumberOfArrays()):
        arrayName = data.GetArrayName(arrayIdx)
        items.append(
          (
            str(self.pAttribute)+'_'+arrayName,
            arrayName,
            arrayName,
            icons[attributeIdx],
            len(items),
          )
        )
    return items

  def update_value(self,context):
    if self.arrayEnums=='None':
      self.pAttribute = 0
      self.pName = 'None'
    else:
      temp = self.arrayEnums.split('_',1)
      self.pAttribute = int(temp[0])
      self.pName = temp[1]
    self.node.id_data.update()

  arrayEnums: bpy.props.EnumProperty(
    name="Arrays",
    items=getArrayEnums,
    update=update_value
  )

  def draw(self, context, layout, node, text):
    if self.is_output or self.is_linked:
        layout.label(text=text)
    else:
        layout.prop(self, "arrayEnums", text=text)

  def draw_color(self, context, node):
    return (0, 163/255, 225/255, 1)

EXPORTS.append(VTKB_NodeSocketArray)

################################################################################
class VTKB_NodeSocketEnum(bpy.types.NodeSocketInt):
  bl_idname = "VTKB_NodeSocketEnum"
  bl_label = "Enum Socket"

  def toggleVis(self,context):
    for s in self.node.inputs:
      s.hide = self.mybool

  def getEnums(self,context):
    return [(x,x.split('_')[1],'') for x in self.enums.split(';')]

  def setEnums(self,enums,default_value):
    self.enums = ';'.join([str(value)+'_'+label for (value,label) in enums])
    for (value,label) in enums:
      if value==default_value:
        self.enum = str(value)+'_'+label

  def getEnumAsInt(self):
    return int(self.enum.split('_')[0])

  enum: bpy.props.EnumProperty(name='', default=0, items=getEnums)
  enums: bpy.props.StringProperty(name='', default='Bob;Test;Array')

  def draw(self, context, layout, node, text):
    layout.label(text=text)
    layout.prop(self,'enum')

  def draw_color(self, context, node):
    return (0, 0.5, 0, 1)

EXPORTS.append(VTKB_NodeSocketEnum)

################################################################################

def export():
  return EXPORTS
