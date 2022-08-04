import bpy

from .VTKB_Node import VTKB_Node

import vtk
import topologytoolkit as ttk

class ErrorObserver:
  def __init__(self,vtkAlgorithm):
    self.vtkAlgorithm = vtkAlgorithm
    self.ErrorOccurred = False
    self.ErrorMessage = None
    self.CallDataType = 'string0'

  def __call__(self, obj, event, message):
    VTKB_NodeAlgorithm.getNode(self.vtkAlgorithm).setStatus('error')
    self.ErrorOccurred = True
    self.ErrorMessage = message

class VTKB_NodeAlgorithm(VTKB_Node):

  @classmethod
  def poll(cls, ntree):
    return ntree.bl_idname == 'VTKB_Tree'

  # static member variable storing all instantiated vtkAlgorithms
  vtkAlgorithms = {}

  @staticmethod
  def getNode(vtkAlgorithm):
    try:
      return eval(vtkAlgorithm.node_path)
    except:
      return None

  def getVtkAlgorithm(self):
    return VTKB_NodeAlgorithm.vtkAlgorithms.get( self.getKey() )

  @staticmethod
  def ready(vtkAlgorithm):
    for i in range(vtkAlgorithm.GetNumberOfInputPorts()):
      if vtkAlgorithm.GetInputPortInformation(i).Has(vtkAlgorithm.INPUT_IS_OPTIONAL()):
        continue
      if vtkAlgorithm.GetNumberOfInputConnections(i)<1:
        return False
    return True

  @staticmethod
  def syncVtkAlgorithms():
    for _,(a,p) in VTKB_NodeAlgorithm.vtkAlgorithms.items():
      if VTKB_NodeAlgorithm.ready(a):
        node = VTKB_NodeAlgorithm.getNode(a)
        try:
          p['ErrorObserver'].ErrorOccurred = False
          a.Update()
          if not p['ErrorObserver'].ErrorOccurred:
            node.setStatus('up-to-date')
        except:
          node.setStatus('error')

  def syncVtkProperties(self):
    a,p = self.getVtkAlgorithm()

    for template in self.inputTemplates:
      if template.type == 'VTKB_NodeSocketDataObject':
        continue

      s = self.inputs[template.name]
      prop = p[template.name]
      v = None
      if template.type == 'VTKB_NodeSocketArray':
        v = [s.pIdx,s.pPort, s.pConnection,s.pAttribute,s.pName]
      elif template.type == 'NodeSocketVector':
        v = [s.default_value[0],s.default_value[1],s.default_value[2]]
      elif template.type == 'VTKB_NodeSocketEnum':
        v = s.getEnumAsInt()
      else:
        v = s.default_value

      if prop.value==v:
        continue

      prop.value = v
      self.setStatus('out-of-date')
      # print('update-prop',self.name+'_'+template.name+'_'+str(v))
      if template.method=='SetInputArrayToProcess':
        a.SetInputArrayToProcess(*v)
      elif type(v) == list:
          try:
            getattr(a,template.method)( v )
          except:
            getattr(a,template.method)( [int(i) for i in v] )
      else:
          try:
            getattr(a,template.method)( v )
          except:
            getattr(a,template.method)( int(v) )
          # getattr(a,template.method)( v )



  def syncVtkConnections(self):
    iAlgorithm,_ = self.getVtkAlgorithm()

    # make sure that every graph connection is represented in vtk
    for iSocket in self.inputs:
      if iSocket.bl_idname!='VTKB_NodeSocketDataObject':
        continue
      iPortIdx = iSocket.index

      for link in iSocket.links:
        oSocket = link.from_socket
        if oSocket.bl_idname!='VTKB_NodeSocketDataObject':
          print('ERROR')
        oNode = link.from_node
        oPortIdx = oSocket.index
        found = False
        for iConnectionIdx in range(iAlgorithm.GetNumberOfInputConnections(iPortIdx)):
          oAlgorithmPort = iAlgorithm.GetInputConnection(iPortIdx,iConnectionIdx)

          if oAlgorithmPort.GetIndex()==oPortIdx and oNode.getKey()==VTKB_NodeAlgorithm.getNode(oAlgorithmPort.GetProducer()).getKey():
            found = True
        if not found:
          oAlgorithm,_ = oNode.getVtkAlgorithm()
          # print('link-add',oNode.name+'('+str(oPortIdx)+')'+'_'+self.name+'('+str(iPortIdx)+')')
          iAlgorithm.SetInputConnection(iPortIdx,oAlgorithm.GetOutputPort(oPortIdx))
          self.setStatus('out-of-date')

    # make sure that every vtk connection is represented in graph
    for iPortIdx in range(iAlgorithm.GetNumberOfInputPorts()):
      iSocket = self.inputs.items()[iPortIdx][1]
      # note: it is possible that there exists no socket if the input port is optional
      if not iSocket:
        continue
      for iConnectionIdx in range(iAlgorithm.GetNumberOfInputConnections(iPortIdx)):
        oAlgorithmPort = iAlgorithm.GetInputConnection(iPortIdx,iConnectionIdx)
        oPortIdx = oAlgorithmPort.GetIndex()
        oAlgorithm = oAlgorithmPort.GetProducer()
        oNode = VTKB_NodeAlgorithm.getNode(oAlgorithm)

        found = False
        for link in iSocket.links:
          if link.from_node.getKey()==oNode.getKey() and link.from_socket.index==oPortIdx:
            found = True

        if not found:
          # print('link-remove',oNode.name+'('+str(oPortIdx)+')'+'_'+self.name+'('+str(iPortIdx)+')')
          iAlgorithm.RemoveInputConnection(iPortIdx,iConnectionIdx)
          self.setStatus('out-of-date')

  def registerVtkAlgorithm(self):
    k = self.getKey()
    a = self.getVtkAlgorithm()
    if a:
      return a

    if self.bl_label.startswith('ttk'):
      a = getattr(ttk,self.bl_label,None)()
    else:
      a = getattr(vtk,self.bl_label,None)()

    if not a:
      print('REGISTRY ERROR: Unable to create vtkAlgorithm for node')

    a.node_path = self.getPath()
    p = {}
    for template in self.inputTemplates:
      templateCopy = template.copy()
      templateCopy.value = None
      p[templateCopy.name] =  templateCopy
    VTKB_NodeAlgorithm.vtkAlgorithms[k] = (a,p)

    e = ErrorObserver(a)
    a.GetExecutive().AddObserver('ErrorEvent', e)
    p['ErrorObserver'] = e

  def unregisterVtkAlgorithm(self):
    k = self.getKey()
    a = self.getVtkAlgorithm()
    if a:
      del VTKB_NodeAlgorithm.vtkAlgorithms[k]

  @staticmethod
  def deleteVtkAlgorithmOrphans():
    toDelete = []
    for k,(a,p) in VTKB_NodeAlgorithm.vtkAlgorithms.items():
      node = VTKB_NodeAlgorithm.getNode(a)
      if not node:
        toDelete.append(k)

    for k in toDelete:
      del VTKB_NodeAlgorithm.vtkAlgorithms[k]
