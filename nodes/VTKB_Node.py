import bpy

class VTKB_Node(bpy.types.Node):

  @classmethod
  def poll(cls, ntree):
    return ntree.bl_idname == 'VTKB_Tree'

  def getKey(self):
    return self.as_pointer()

  def getPath(self):
    return (
      'bpy.data.node_groups['
      + repr(self.id_data.name)
      + '].nodes['
      + repr(self.name)
      + ']'
    )

  def init(self, context):
    self.initializeInputSockets()
    self.initializeOutputSockets()

  def setStatus(self,status):
    self.use_custom_color = True
    self.color = {
      'up-to-date': (0.2, 0.2, 0.2),
      'out-of-date': (0.4, 0.4, 0.4),
      'error': (0.36, 0., 0.),
    }[status]

  def initializeInputSockets(self):
    w = self.width

    for template in self.inputTemplates:
      s = self.inputs.new(template.type, template.name)

      match template.type:
        case 'VTKB_NodeSocketDataObject':
          s.display_shape = 'DIAMOND'
          s.index = template.value
        case 'VTKB_NodeSocketEnum':
          s.setEnums(template.extras['enumItems'],template.value)
        case 'VTKB_NodeSocketArray':
          self.width=w*2
          s.pIdx = template.value[0]
          s.pPort = template.value[1]
          s.pConnection = template.value[2]
          s.pAttribute = template.value[3]
          s.pName = template.value[4]
        case _:
          if template.type == 'NodeSocketString':
            self.width=w*2
          if template.value!=None:
            s.default_value = template.value

  def initializeOutputSockets(self):
    for template in self.outputTemplates:
      s = self.outputs.new(template.type, template.name)
      if template.type == 'VTKB_NodeSocketDataObject':
        s.display_shape = 'DIAMOND'
        s.index = template.value


