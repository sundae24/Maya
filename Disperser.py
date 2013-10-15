import pymel.core as pm
import random

class JJ_DisperserWindow():
    @classmethod
    def showUI(cls):
        """Instantiate the pose manager window"""
        win = cls()
        win.create()
        return win

    def __init__(self):
        """Initialize data attributes"""
        self.window = 'jj_disperserWindow'
        self.title = 'Disperser Window'
        self.size = (380, 380)
        self.sourceObj = None
        self.targetObjs = None

    def create(self):
        if pm.window(self.window, exists=True):
            pm.deleteUI(self.window)
        pm.window(self.window, t=self.title)

        # source & targets
        pm.rowColumnLayout(nc=3,cal=[(1,'right')], cw=[(1,80),(2,200),(3,100)])
        pm.text(l='Source: ')
        self.sourceObjTf = pm.textField()
        pm.button(l='Select', c=self.selectSource)
        pm.text(l='Target(s): ')
        self.targetObjsTf = pm.textField()
        pm.button(l='Select', c=self.selectTarget)
        pm.setParent('..')

        # number
        pm.rowColumnLayout(w=self.size[0])
        self.copyNum = pm.intSliderGrp(l='Copies: ', v=10, cw3=[80,80,220],
                                       min=1, max=500, fmx=5000, f=True)
        pm.separator(h=10, st='in')

        # rotation
        pm.rowColumnLayout(nc=2, cal=[(1,'right')], cw=[(1,80), (2,300)])
        pm.text(l='Rotation: ')
        self.rotationModeRC = pm.radioCollection()
        self.rotBtnFixed = pm.radioButton(l='Fixed', sl=True)
        pm.text(l='')
        self.rotBtnAlign = pm.radioButton(l='Align with Target')
        pm.text(l='')
        self.rotBtnRand = pm.radioButton(l='Random',
                                         onc=lambda *args: self.rotationRange.setEnable(True),
                                         ofc=lambda *args: self.rotationRange.setEnable(False))
        pm.setParent('..')
        self.rotationRange = pm.floatFieldGrp(l='Range: ', nf=3, v1=30, v2=30, v3=30,
                                              cw4=[80,100,100,100], en=False)
        pm.separator(h=10, st='in')

        # scale
        pm.rowColumnLayout(nc=2, cal=[(1,'right')], cw=[(1,80), (2,300)])
        pm.text(l='Scale: ')
        self.scaleModeRC = pm.radioCollection()
        self.scaleBtnFixed = pm.radioButton(l='Fixed', sl=True)
        pm.text(l='')
        self.scaleBtnRand = pm.radioButton(l='Random',
                                           onc=lambda *args: self.scaleRange.setEnable(True),
                                           ofc=lambda *args: self.scaleRange.setEnable(False))
        pm.setParent( '..' )
        self.scaleRange = pm.floatFieldGrp(l='Min Max: ', nf=2, v1=1, v2=1,
                                           cw3=[80,100,100], en=False)
        pm.separator(h=10, st='in')

        # disperse button
        pm.button(l='Disperse', c=self.disperse, w=380, al='center')

        pm.showWindow(self.window)

    def selectSource(self, *args):
        """Called when the select source button is pressed"""
        sourceList = pm.ls(sl=True, tr=True)
        if len(sourceList) != 1:
            self.sourceObjTf.setText('Please select one object')
        else:
            self.sourceObj = sourceList[0]
            self.sourceObjTf.setText(str(self.sourceObj))

    def selectTarget(self, *args):
        """Called when the select target button is pressed"""
        self.targetObjs = pm.ls(sl=True, tr=True)
        if len(self.targetObjs) < 1:
            self.targetObjsTf.setText('Please select at least one object')
            return
        targetsTx = ', '.join([str(x) for x in self.targetObjs])
        self.targetObjsTf.setText(targetsTx)
        self.targetVertNumList = []
        targetVerts = 0
        for obj in self.targetObjs:
            targetVertNum = pm.polyEvaluate(obj, v=True)
            self.targetVertNumList.append(targetVertNum)
            targetVerts += targetVertNum
        self.vertIndexList = [v for v in range(targetVerts)]

    def disperse(self, *args):
        """Called when the disperse button is pressed"""
        if self.sourceObj == None or self.targetObjs == None:
            pm.confirmDialog(t='Error', b=['OK'],
                m='Please make sure source and targets are selected.')
            return

        # get copy number
        copyNum = self.copyNum.getValue()
        copyNum = min(copyNum, len(self.vertIndexList))

        # get rotation
        rotationMode = self.rotationModeRC.getSelect()
        rotationMode = pm.control(rotationMode, q=True, fpn=True)
        if rotationMode == self.rotBtnRand:
            origRot = pm.xform(self.sourceObj, ro=True, q=True)
            rotRange = self.rotationRange.getValue()

        # get scale
        scaleMode = self.scaleModeRC.getSelect()
        scaleMode = pm.control(scaleMode, q=True, fpn=True)
        if scaleMode == self.scaleBtnRand:
            scaleRange = self.scaleRange.getValue()

        # make copies
        randVertIndexList = random.sample(self.vertIndexList, copyNum)
        for i in randVertIndexList:
            newObj = pm.duplicate(self.sourceObj, n='%s_copy'%self.sourceObj)
            # decide which target the random vert index falls on
            vertSum = 0
            targetIndex = 0
            targetVertIndex = 0
            for j, k in enumerate(self.targetVertNumList):
                vertSum += k
                if i + 1 <= vertSum:
                    targetIndex = j
                    targetVertIndex = i - (vertSum - k)
                    break
            # apply scale
            if scaleMode == self.scaleBtnRand:
                randScale = random.uniform(scaleRange[0], scaleRange[1])
                pm.xform(newObj, s=(randScale,randScale,randScale))
            # apply rotation
            if rotationMode == self.rotBtnAlign: # normal constraint
                pm.normalConstraint(self.targetObjs[targetIndex], newObj, aim=(0,0,1), u=(0,1,0))
            elif rotationMode == self.rotBtnRand:
                newRotX = random.uniform(origRot[0]-rotRange[0]/2,origRot[0]+rotRange[0]/2)
                newRotY = random.uniform(origRot[1]-rotRange[1]/2,origRot[1]+rotRange[1]/2)
                newRotZ = random.uniform(origRot[2]-rotRange[2]/2,origRot[2]+rotRange[2]/2)
                pm.xform(newObj, ro=(newRotX,newRotY,newRotZ))
            rotatePivot = pm.xform(newObj, rp=True, q=True)
            newPos = pm.pointPosition('%s.vtx[%d]'%(self.targetObjs[targetIndex],targetVertIndex))
            posOffset = [newPos[0]-rotatePivot[0], newPos[1]-rotatePivot[1], newPos[2]-rotatePivot[2]]
            pm.xform(newObj, t=posOffset)
            # remove constraint after translation
            if rotationMode == self.rotBtnAlign:
                pm.delete(newObj, cn=True)
