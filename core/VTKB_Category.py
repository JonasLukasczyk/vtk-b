import nodeitems_utils

class VTKB_Category(nodeitems_utils.NodeCategory):

  categories= {}

  @staticmethod
  def addItem(category,node):
    if not VTKB_Category.categories.get(category):
      VTKB_Category.categories[category] = []
    VTKB_Category.categories[category].append( node.bl_idname )

  @staticmethod
  def generate():
    node_categories = [];
    keys = list(VTKB_Category.categories.keys())
    keys.sort()
    for key in keys:
      items = VTKB_Category.categories[key]
      if len(items)<1:
        continue
      items.sort()
      node_categories.append(
        VTKB_Category(
          key, key,
          items=[nodeitems_utils.NodeItem(item) for item in items]),
      )
    return node_categories

  @classmethod
  def poll(cls, context):
    return context.space_data.tree_type == 'VTKB_Tree'
