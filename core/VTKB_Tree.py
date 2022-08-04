import bpy

from .. import registry
from . import VTKB_Colormaps

class VTKB_Tree(bpy.types.NodeTree):
  bl_label = "VTKB Tree"
  bl_icon = 'NETWORK_DRIVE'

  NEEDS_UPDATE: bpy.props.BoolProperty(default=True)
  def update(self):
    self.NEEDS_UPDATE = True

  def triggerPipelineUpdate(self,context):
    for tree in bpy.data.node_groups:
      tree.update()

  vtkLocation: bpy.props.FloatVectorProperty(default=(0,0,0), update=triggerPipelineUpdate)
  vtkRotation: bpy.props.FloatVectorProperty(default=(0,0,0), update=triggerPipelineUpdate)
  vtkScale: bpy.props.FloatProperty(default=1, update=triggerPipelineUpdate)

  def applyColormap(self,context):
    if len(context.selected_nodes)<1:
      return
    ramp = context.selected_nodes[0]
    if ramp.bl_idname!='ShaderNodeValToRGB':
      return

    for i in range(1,len(ramp.color_ramp.elements))[::-1]:
      ramp.color_ramp.elements.remove(ramp.color_ramp.elements[i])

    controlPoints = VTKB_Colormaps.COLOR_MAPS[self.Colormaps]

    ramp.color_ramp.elements[0].position = controlPoints[0]
    ramp.color_ramp.elements[0].color = (controlPoints[1],controlPoints[2],controlPoints[3],1)
    for i,idx in enumerate(range(4,len(controlPoints),4)):
      ramp.color_ramp.elements.new(controlPoints[idx])
      ramp.color_ramp.elements[i+1].color = (controlPoints[idx+1],controlPoints[idx+2],controlPoints[idx+3],1)

  Colormaps : bpy.props.EnumProperty(
    items=[
      ('Accent','Accent',''),
      ('Blues','Blues',''),
      ('BrBG','BrBG',''),
      ('BuGn','BuGn',''),
      ('BuPu','BuPu',''),
      ('Dark2','Dark2',''),
      ('GnBu','GnBu',''),
      ('Greens','Greens',''),
      ('Greys','Greys',''),
      ('OrRd','OrRd',''),
      ('Oranges','Oranges',''),
      ('PRGn','PRGn',''),
      ('Paired','Paired',''),
      ('Pastel1','Pastel1',''),
      ('Pastel2','Pastel2',''),
      ('PiYG','PiYG',''),
      ('PuBu','PuBu',''),
      ('PuBuGn','PuBuGn',''),
      ('PuOr','PuOr',''),
      ('PuRd','PuRd',''),
      ('Purples','Purples',''),
      ('RdBu','RdBu',''),
      ('RdGy','RdGy',''),
      ('RdPu','RdPu',''),
      ('RdYlBu','RdYlBu',''),
      ('RdYlGn','RdYlGn',''),
      ('Reds','Reds',''),
      ('Set1','Set1',''),
      ('Set2','Set2',''),
      ('Set3','Set3',''),
      ('Spectral','Spectral',''),
      ('YlGn','YlGn',''),
      ('YlGnBu','YlGnBu',''),
      ('YlOrBr','YlOrBr',''),
      ('YlOrRd','YlOrRd',''),
      ('autumn','autumn',''),
      ('binary','binary',''),
      ('bone','bone',''),
      ('cool','cool',''),
      ('copper','copper',''),
      ('flag','flag',''),
      ('gist_earth','gist_earth',''),
      ('gist_gray','gist_gray',''),
      ('gist_heat','gist_heat',''),
      ('gist_ncar','gist_ncar',''),
      ('gist_rainbow','gist_rainbow',''),
      ('gist_stern','gist_stern',''),
      ('gist_yarg','gist_yarg',''),
      ('gray','gray',''),
      ('hot','hot',''),
    ],
    update=applyColormap
  )

registry.UI_CLASSES.append(VTKB_Tree)
