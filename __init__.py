bl_info = {
  "name": "VTK-Blender, VTK Nodes for Blender",
  "author": "JL",
  "version": (0, 1),
  "blender": (3, 2, 0),
  "location": "VTKB Node Tree Editor > New",
  "description": "Create and execute VTK pipelines in Blender Node Editor",
  "warning": "Experimental",
  # "wiki_url": "https://github.com/tkeskita/VTKBNodes",
  # "tracker_url": "https://github.com/tkeskita/VTKBNodes/issues",
  "support": "COMMUNITY",
  "category": "Node",
}

import sys
sys.path.insert(0,'/home/jones/external/projects/paraview/install/lib/python3.10/site-packages')

import bpy
import nodeitems_utils

from . import registry
from . import core
from . import sockets
from . import nodes

nodes.VTKB_Factory.generateVTKBNodesFromXMLS()

from bpy.app.handlers import persistent

from .nodes.VTKB_NodeAlgorithm import VTKB_NodeAlgorithm

@persistent
def execute(scene,graph):

  for tree in bpy.data.node_groups:
    if tree.bl_idname != 'VTKB_Tree':
      continue

    if not tree.NEEDS_UPDATE:
      continue

    print('[VTK-B] EXECUTE TREE',tree.name)

    VTKB_NodeAlgorithm.deleteVtkAlgorithmOrphans()

    algorithmNodes = [node for node in tree.nodes if issubclass(node.__class__,VTKB_NodeAlgorithm)]

    for node in algorithmNodes:
      node.registerVtkAlgorithm()
    for node in algorithmNodes:
      node.syncVtkProperties()
      node.syncVtkConnections()
    VTKB_NodeAlgorithm.syncVtkAlgorithms()

    for node in algorithmNodes:
      for socket in node.outputs:
        nodes.VTKB_NodeConverters.convertVtkDataObjectFromSocket(socket)

    converterNodes = [node for node in tree.nodes if issubclass(node.__class__,nodes.VTKB_NodeConverters.VTKB_NodeConverters)]
    for node in converterNodes:
      node.convert()

    tree.NEEDS_UPDATE = False

if execute not in bpy.app.handlers.depsgraph_update_post:
  bpy.app.handlers.depsgraph_update_post.append(execute)
if execute not in bpy.app.handlers.load_post:
  bpy.app.handlers.load_post.append(execute)

def register():
  print('[VTK-B] Registering Classes')
  for cls in registry.UI_CLASSES:
    print('reg', cls)
    bpy.utils.register_class(cls)
  nodeitems_utils.register_node_categories(
    'VTKB_NODES',
    core.VTKB_Category.VTKB_Category.generate()
  )

def unregister():
  print('[VTK-B] Unregistering Classes')

  nodeitems_utils.unregister_node_categories('VTKB_NODES')
  for cls in registry.UI_CLASSES[::-1]:
    print('unreg', cls)
    bpy.utils.unregister_class(cls)

if __name__ == "__main__":
  register()
