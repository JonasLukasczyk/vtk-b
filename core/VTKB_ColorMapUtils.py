import bpy

import os

from .. import registry
from . import VTKB_ColorMaps

################################################################################
class VTKB_PanelShaderEditor(bpy.types.Panel):
    bl_idname = "NODEEDITOR_PT_shader_editor"
    bl_label = "Hello World"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = "object"

    def draw(self, context):
        self.layout.label(text="Hello World")
        prop_grp = context.window_manager.CreateColorMapOperatorProps
        # op = self.layout.operator('opr.create_color_map_operator', text='Create Color Map')
        self.layout.prop(prop_grp, 'ColorMaps')

registry.UI_CLASSES.append(VTKB_PanelShaderEditor)

################################################################################
class CreateColorMapOperatorProps(bpy.types.PropertyGroup):

  def applyColorMap(self,context):
    if len(context.selected_nodes)<1:
      return
    ramp = context.selected_nodes[0]
    if ramp.bl_idname!='ShaderNodeValToRGB':
      return

    for i in range(1,len(ramp.color_ramp.elements))[::-1]:
      ramp.color_ramp.elements.remove(ramp.color_ramp.elements[i])

    controlPoints = VTKB_ColorMaps.COLOR_MAPS[self.ColorMaps]

    ramp.color_ramp.elements[0].position = controlPoints[0]
    ramp.color_ramp.elements[0].color = (controlPoints[1],controlPoints[2],controlPoints[3],1)
    for i,idx in enumerate(range(4,len(controlPoints),4)):
      ramp.color_ramp.elements.new(controlPoints[idx])
      ramp.color_ramp.elements[i+1].color = (controlPoints[idx+1],controlPoints[idx+2],controlPoints[idx+3],1)


  ColorMaps : bpy.props.EnumProperty(
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
    update=applyColorMap
  )

registry.UI_CLASSES.append(CreateColorMapOperatorProps)


# maps = {}
# let cmapName = null
# let cmapData = []
# for(var line of x.split('\n')){
#   data = line.split('"')
#   if(data[0]==='<ColorMap name='){
#     cmapName = data[1]
#     cmapData = []
#   } else if(data[0]==='</ColorMap>') {
#     maps[cmapName] = cmapData
#   } else {
#     cmapData.push(parseFloat(data[1]))
#     cmapData.push(parseFloat(data[5]))
#     cmapData.push(parseFloat(data[7]))
#     cmapData.push(parseFloat(data[9]))
#   }
# }

# out ='COLOR_MAPS = {\n'
# for(cmapname in maps){
#   cmap = maps[cmapname]
#   out += "'"+cmapname+"':["

#   console.log(cmapname,cmap.length)

#   for(i=0;i<4;i++){
#     out += cmap[i].toFixed(4) +','
#   }

#   for(i=1; i<16; i++)
#     for(j=0;j<4;j++){
#       out += cmap[i*4*16+j].toFixed(4)+','
#     }

#   for(i=1020;i<1024;i++){
#     out += cmap[i].toFixed(4) +','
#   }
#   out += "],\n"
# }
# out += '}'

# console.log(out)
