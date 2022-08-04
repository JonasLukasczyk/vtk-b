import bpy

import os

from .. import registry

################################################################################
class VTKB_Panel(bpy.types.Panel):
    bl_idname = "NODEEDITOR_PT_VTKB"
    bl_label = "VTK-B"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_context = "object"

    firstTree = None

    def draw(self, context):
      if not VTKB_Panel.firstTree:
        for tree in bpy.data.node_groups:
          if tree.bl_idname=='VTKB_Tree':
            VTKB_Panel.firstTree = tree
            break

      self.layout.label(text='Generate Colormap')
      self.layout.prop(VTKB_Panel.firstTree, 'Colormaps', text='')
      self.layout.label(text='Blender Conversion')
      self.layout.prop(VTKB_Panel.firstTree, 'vtkLocation', text='Location')
      self.layout.prop(VTKB_Panel.firstTree, 'vtkRotation', text='Rotation')
      self.layout.prop(VTKB_Panel.firstTree, 'vtkScale', text='Scale')

registry.UI_CLASSES.append(VTKB_Panel)


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
