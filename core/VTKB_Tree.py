import bpy

class VTKB_Tree(bpy.types.NodeTree):
  bl_label = "VTKB Tree"
  bl_icon = 'NETWORK_DRIVE'

  NEEDS_UPDATE: bpy.props.BoolProperty(default=True)

  def update(self):
    self.NEEDS_UPDATE = True