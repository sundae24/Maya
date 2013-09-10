import maya.cmds as cmds
import maya.OpenMaya as OM
import random

# one source, multiple target surfaces
class Disperser():
    
    sourceObj = None
    targetObjs = None
    
    # GUI
    def __init__(self):
        if cmds.window("disperser", exists=True):
            cmds.deleteUI("disperser")
        cmds.window("disperser", t = "Disperser")
		
		# source & targets
        cmds.rowColumnLayout(nc=3,cal=[(1,"right")], cw=[(1,80),(2,200),(3,100)])
        cmds.text(l="Source: ")
        cmds.textField("sourceObj")
        cmds.button("sourceButton", l="Select", c=self.selectSource)
        cmds.text(l="Target(s): ")
        cmds.textField("targetObjs")
        cmds.button("targetsButton", l="Select", c=self.selectTarget)
        cmds.setParent("..")
        
        # number
        cmds.rowColumnLayout(w=380)        
        cmds.intSliderGrp("copyNum", l="Copies: ", v=10, cw3=[80,80,220], min=1, max=500, fmx=5000, f=True)
        cmds.separator(h=10, st='in')
        
        # rotation
        cmds.rowColumnLayout(nc=2, cal=[(1,"right")], cw=[(1,80), (2,300)])
        cmds.text(l="Rotation: ")
        cmds.radioCollection("rotation")
        cmds.radioButton("rotButFixed", l='Fixed', sl=True)
        cmds.text(l="")
        cmds.radioButton("rotButAlign", l='Align with Target')
        cmds.text(l="")
        cmds.radioButton("rotButRand", l='Random', onc="cmds.floatFieldGrp('rotationRange', e=True, en=True)", ofc="cmds.floatFieldGrp('rotationRange', e=True, en=False)")
        cmds.setParent("..")
        cmds.floatFieldGrp("rotationRange", l="Range: ", nf=3, v1=30, v2=30, v3=30, cw4=[80,100,100,100], en=False)
        cmds.separator(h=10, st='in')
        
        # scale
        cmds.rowColumnLayout(nc=2, cal=[(1,"right")], cw=[(1,80), (2,300)])
        cmds.text(l="Scale: ")
        cmds.radioCollection("scale")
        cmds.radioButton("scaleButFixed", l='Fixed', sl=True)
        cmds.text(l="")
        cmds.radioButton("scaleButRand", l='Random', onc="cmds.floatFieldGrp('scaleRange', e=True, en=True)", ofc="cmds.floatFieldGrp('scaleRange', e=True, en=False)")
        cmds.setParent( '..' )
        cmds.floatFieldGrp("scaleRange", l="Min Max: ", nf=2, v1=1, v2=1, cw3=[80,100,100], en=False)
        cmds.separator(h=10, st='in')
        
        # disperse button
        cmds.button("disperseBut", l="Disperse", c=self.disperse, w=380, al="center")
        
        cmds.showWindow("disperser")
    
    # one object allowed as source
    def selectSource(self, *args):
        sourceList = cmds.ls(sl=True, tr=True)
        if len(sourceList) > 1 or len(sourceList) == 0:
            cmds.textField("sourceObj", e=True, tx="Please select one object")
        else:
            self.sourceObj = sourceList[0]
            cmds.textField("sourceObj", e=True, tx=self.sourceObj)
    
    # support multiple targets
    def selectTarget(self, *args):
        self.targetObjs = cmds.ls(sl=True, tr=True)
        if len(self.targetObjs) < 1:
            cmds.textField("targetObjs", e=True, tx="Please select at least one object")
            return
        targetsTx=', '.join(self.targetObjs)
        cmds.textField("targetObjs", e=True, tx=targetsTx)
        self.targetVertNumList = []
        targetVerts = 0
        for obj in self.targetObjs:
            targetVertNum = cmds.polyEvaluate(obj, v=True)
            self.targetVertNumList.append(targetVertNum)
            targetVerts += targetVertNum
        self.vertIndexList = [v for v in range(targetVerts)]
        
    # disperse 
    def disperse(self, *args):
        if self.sourceObj == None or self.targetObjs == None:
            OM.MGlobal.displayError("Please make sure source and target(s) are selected above.")
            return
        
        # get copy number
        copyNum = cmds.intSliderGrp("copyNum", q=True, v=True)
        if copyNum > len(self.vertIndexList):
            OM.MGlobal.displayWarning("Not enough vertices on target(s) to make %d copies!"%copyNum)
            copyNum = len(self.vertIndexList)
        
        # get rotation
        rotationMode = cmds.radioCollection("rotation", q=True, sl=True)
        if rotationMode == "rotButRand":
            origRot = cmds.xform(self.sourceObj, ro=True, q=True)
            rotRange = cmds.floatFieldGrp("rotationRange", q=True, v=True)
        
        # get scale
        scaleMode = cmds.radioCollection("scale", q=True, sl=True)
        if scaleMode == "scaleButRand":
            scaleRange = cmds.floatFieldGrp("scaleRange", q=True, v=True)
            
        # make copies
        randVertIndexList = random.sample(self.vertIndexList, copyNum)
        for i in range(copyNum):
            newObj = cmds.duplicate(self.sourceObj, n="%s_copy"%self.sourceObj)
            # decide which target the random vert index falls on
            vertSum = 0
            targetIndex = 0
            targetVertIndex = 0
            for j in range(len(self.targetVertNumList)):
                vertSum += self.targetVertNumList[j]
                if randVertIndexList[i]+1 <= vertSum:
                    targetIndex = j
                    targetVertIndex = randVertIndexList[i] - (vertSum - self.targetVertNumList[j])
                    #print "targetIndex: ", targetIndex, " vertIndex: ", targetVertIndex
                    break
            # apply scale
            if scaleMode == "scaleButRand":
                randScale = random.uniform(scaleRange[0], scaleRange[1])
                cmds.xform(newObj, s=(randScale,randScale,randScale))
            # apply rotation
            if rotationMode == "rotButAlign": # normal constraint
                cmds.normalConstraint(self.targetObjs[targetIndex], newObj, aim=(0,0,1), u=(0,1,0))
            elif rotationMode == "rotButRand":
                newRotX = random.uniform(origRot[0]-rotRange[0]/2,origRot[0]+rotRange[0]/2)
                newRotY = random.uniform(origRot[1]-rotRange[1]/2,origRot[1]+rotRange[1]/2)
                newRotZ = random.uniform(origRot[2]-rotRange[2]/2,origRot[2]+rotRange[2]/2)
                cmds.xform(newObj, ro=(newRotX,newRotY,newRotZ))
            rotatePivot = cmds.xform(newObj, rp=True, q=True)
            newPos = cmds.pointPosition("%s.vtx[%d]"%(self.targetObjs[targetIndex],targetVertIndex))
            posOffset = [newPos[0]-rotatePivot[0], newPos[1]-rotatePivot[1], newPos[2]-rotatePivot[2]]
            cmds.xform(newObj, t=posOffset)
            if rotationMode == "rotButAlign": # remove constraint after translation
                cmds.delete(newObj, cn=True)
        
        
Disperser()