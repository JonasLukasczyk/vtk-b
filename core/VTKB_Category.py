import nodeitems_utils

class VTKB_Category(nodeitems_utils.NodeCategory):

  categories= {}

  @staticmethod
  def addItem(category,node):
    if not VTKB_Category.categories.get(category):
      VTKB_Category.categories[category] = []
    VTKB_Category.categories[category].append(
      nodeitems_utils.NodeItem(node.bl_idname)
    )

  @staticmethod
  def generate():
    node_categories = [];
    for n,items in VTKB_Category.categories.items():
      node_categories.append(
        VTKB_Category(n, n, items=items),
      )
    return node_categories

  @classmethod
  def poll(cls, context):
    return context.space_data.tree_type == 'VTKB_Tree'
