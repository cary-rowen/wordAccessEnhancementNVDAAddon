# appModules\winword\ww.collection.py
#A part of wordAccessEnhancement add-on
#Copyright (C) 2019 paulber19
#This file is covered by the GNU General Public License.


import addonHandler
addonHandler.initTranslation()
import api
import wx
import gui
import ui
import core
from  eventHandler import queueEvent
import queueHandler
import time
import textInfos
import speech
import controlTypes
from .ww_wdConst import wdActiveEndPageNumber , wdFirstCharacterLineNumber , wdWord, wdChar
from .ww_wdConst import wdGoToFirst, wdGoToLast, wdGoToNext, wdGoToPrevious, wdStory
import sys
import os
_curAddon = addonHandler.getCodeAddon()
path = os.path.join(_curAddon.path, "shared")
sys.path.append(path)
from ww_utils import printDebug
from ww_py3Compatibility import _unicode
del sys.path[-1]

def convertPixelToUnit(nbPixel):
	unit = float(_("28.35"))
	return  nbPixel/unit

class CollectionElement(object):
	def __init__(self, parent, obj):
		printDebug("CollectionElement init")
		self.parent = parent
		self.doc = obj.application.ActiveDocument
		self.obj = obj
		
	def setLineAndPageNumber(self, rangeObj  = None):
		if rangeObj is None:
			rangeObj= self.doc.range(self.start, self.start)
		# Informations method is not available when Word is not registered.
		try:
			self.line = rangeObj.Information(wdFirstCharacterLineNumber )
			self.page = rangeObj.Information(wdActiveEndPageNumber )
		except:
			self.line = ""
			self.page = ""


	def goTo(self):
		printDebug ("Collection goTo")
		r = self.doc.range(self.start, self.start)
		r.select()
		r.collapse()

	def delete(self):
		self.obj.Delete()


	def reportText(self):
		ui.message(self.text)

class Collection(object):
	_elementUnit = textInfos.UNIT_LINE
	_instance = None
	_delay = 4
	def __new__(cls, *args, **kwargs):
		if Collection._instance is not None:
			if getattr(Collection._instance,'dialog',None)and  Collection._instance.dialog:
				Collection._instance.dialog.Destroy()
		return super(Collection, cls).__new__(cls)
		
	def __init__(self, parent, obj):
		printDebug ("Collection init: rangeType = %s" %self.rangeType)
		Collection._instance = self
		self.wordApp = obj._get_WinwordApplicationObject()
		self.doc = self.wordApp.ActiveDocument
		self.selection = self.wordApp.Selection

		noElementMessages= {
			"focus": _("%s at cursor's position"),
			"selection": _("%s in the selection"),
			"document": _("%s in the document"),
			"page": _("%s in the page"),
			"startToFocus": _("%s between  start of document and cursor's position"),
				"focusToEnd" : _("%s between cursor's position and end of document")
				}
		
		(singular, plural) = self._name 
		titles= {
			"focus": _("%s at cursor's position") %singular,
			"selection":  _("%s in the selection") %plural,
			"document": _("%s in the document") %plural,
			"page": _("%s in the page") %plural,
			"startToFocus" : _("%s  between document's start  and cursor's position") %plural,
			"focusToEnd" : _("%s between cursor's position and document's end") %plural
				}

		self.noElementMessage = noElementMessages[self.rangeType] %self.noElement
		self.title= titles[self.rangeType]
		self.parent = parent
		self.collection = self.getElementsInCollection()
	
	def __del__(self):
		Collection._instance = None
		if getattr(self,'dialog',None): 
			self.dialog.Destroy()
	def sayPercentage(self, cur, max, startTime):
		curTime = time.time()
		if curTime - startTime >= self._delay:
			if self.parent.isActive:
				per = int(100*(float(cur)/float(max)))
				speech.speakMessage(_("%s percent") %str(int(per)))
			return  curTime
		return startTime
	
	def getCollectionInRange(self, theRange):
		printDebug("Collection getCollectionInRange: %s" %theRange)
		collection= []
		for item in self._propertyName:
			(property,elementClass) = item
			col =getattr(theRange,property)
			try:
				col =getattr(theRange,property)
			except:
				# no collection for the range
				printDebug ("No collection for the range")
				continue

			#try:
			if True:
				count = col.count
				startTime = time.time()
				for i in range(1, count+1):
					startTime = self.sayPercentage(i, count, startTime)
					# stopped by user?
					if self.parent and self.parent.canceled:
						return []
					collection.append((col[i], elementClass))
			#except:
			else:
				speech.speakMessage(_("Sorry, There are too  many elements to be treated "))
				speech.speakMessage(_("Select smaller part of document"))
				time.sleep(3.0)
				return None

		return collection


	
	def getElementsInCollection(self):
		printDebug("Collection getElementsInCollection")
		objectsInCollection = self.getCollection()
		if objectsInCollection == None:
			return None

		elements = []
		startTime = time.time()
		count = len(objectsInCollection)
		for item in objectsInCollection:
			startTime = self.sayPercentage(objectsInCollection.index(item), count, startTime)
			if self.parent and self.parent.canceled :
				return []
			(obj, elementClass) = item
			element = elementClass(self,  obj )
			try:
				element = elementClass(self,  obj )
				elements.append(element)

			except:
				printDebug ("getElementsInCollection:  except on element = elementClass")
				speech.speakMessage(_("Sorry, There are too  many elements to be treated "))
				time.sleep(2.0)
				return None

		return elements


	def getCollection(self):
		printDebug ("Collection getCollection")
		pleaseWait = True
		if self.rangeType == "selection":
			# elements in a selection
			r = self.doc.range(self.selection.Start, self.selection.End)

		elif self.rangeType == "focus":
			if hasattr(self, "reference"):
				r = self.doc.range(self.reference, self.reference+1)
			else:
				r = self.doc.range(self.selection.Start, self.selection.Start+1)

			pleaseWait = False

		elif self.rangeType == "document":
			start = self.doc.Content.Start
			end = self.doc.Content.End
			r = self.doc.range(start, end)
		elif self.rangeType == "startToFocus":
			start = self.doc.Content.Start
			end = self.selection.Start
			r = self.doc.range(start, end)
		elif self.rangeType == "page":
			r = self.doc.Bookmarks("\page").Range
			
		elif self.rangeType == "focusToEnd":
			start = self.selection.Start
			end = self.doc.Content.End
			r = self.doc.range(start, end)



		if pleaseWait:
			speech.speakMessage(_("Please wait."))
			time.sleep(1.0)
			
		collection = self.getCollectionInRange(r)
		return collection
	
	def refreshItemsList(self):
		return self.collection
	
	def delete(self, element):
		element.delete()
		self.collection.remove(element)
		
	
	def deleteAll(self):
		c = self.collection[:]
		for element in c:
			element.delete()
		self.collection = []
	
	def reportCollection(self, copyToClip, makeChoiceDialog):
		if self.collection == None:
			api.processPendingEvents()
			time.sleep(0.01)
			obj  = api.getFocusObject()
			queueEvent("gainFocus",obj)
			return
		if len(self.collection) == 0:
			gui.messageBox(self.noElementMessage, self.title, wx.OK)
			return
		if copyToClip:
			sText = self.formatInfosForClipboard()
			api.copyToClip(sText)
			speech.speakMessage(_("{name}'s list has been copied to clipboard").format(name= self._name[1]))
			time.sleep(2.0)
		else:
			wx.CallAfter(self.dialogClass.run, self, makeChoiceDialog)
	
	def formatInfosForClipboard(self):
		count = len(self.collection)
		if count == 0:
			return ""
		elif count == 1:
			sTitle = ""
			sSummary = _unicode("{title}: ").format(title = self.title)
		else:
			sSummary = _unicode("{title}: {count}").format(title =self.title, count= count)
			sTitle = _unicode("{name} {index}:")

		sText = sSummary
		for item in self.collection:
			index = self.collection.index(item)+1
			if sTitle != "":
				sText = sText +"\r\n" + sTitle.format(name = self._name[0],index = index)
				
			sText = sText + "\r\n" + item.formatInfos()
		return sText
	
	def reportElements(self):
		printDebug ("Collection reportElement")
		col = self.collection
		if len(col) == 0:
			speech.speakMessage(self.noElementMessage)
			return
		if len(col)  >1:
			speech.speakMessage(_("{count} {element}") .format( count = len(col), element = self._name[0]))
		for  element in col:
			element.reportText()

	def speakContext(self, oldSpeechMode):
		obj = api.getFocusObject()
		if oldSpeechMode != None:
			speech.speechMode = oldSpeechMode
		elementUnit = self._elementUnit
		if elementUnit == None:
			return
		try:
			info=obj.makeTextInfo(textInfos.POSITION_CARET)
		except:
			return
		
		info.expand(elementUnit)
		speech.speakTextInfo(info,reason=controlTypes.REASON_CARET,unit= elementUnit, onlyInitialFields = False)

class ReportDialog(wx.Dialog):
	_defaultLCWidth = 300
	_lcHeightOffset = 5
	def __init__(self, parent,collectionObject):
		printDebug ("ReportDialog init: collectionObject = %s" %collectionObject)
		self.parent = parent
		super(ReportDialog, self).__init__(parent, title=collectionObject.title )
		self.timer = None
		self.collectionObject = collectionObject
		self.wordApp = collectionObject.wordApp
		self.collection = collectionObject.collection[:]
		self.initializeGUI()
		self.doGUI( )


	def initializeGUI (self):
		self.lcLabel = "TCLabel"
		self.lcColumns = (
			("Column1",150),
			("Column2", 150),
			("Column3", 300),
			("Column4", 150)
			)
			
		lcWidth = 0
		for column in self.lcColumns:
			lcWidth = lcWidth + column[1]
			
		self.lcSize = (lcWidth, self._defaultLCSize)

		self.buttons = (
			(100, "Button1",None),
			(101, "Button2", None),
			(102, "Button3", None)
			)

		self.tc1 = {
		"label": "TC1label",
		"size" : (800,200)
		}
		self.tc2 = {
		"label": "TC2Label",
		"size" : (800, 200)
		}


	def doGUI(self):

		mainSizer=wx.BoxSizer(wx.VERTICAL)
		settingsSizer=wx.BoxSizer(wx.VERTICAL)
		entriesSizer=wx.BoxSizer(wx.VERTICAL)
		entriesLabel=wx.StaticText(self,-1,label=self.lcLabel)
		entriesSizer.Add(entriesLabel)
		(h,w) = self.lcSize
		self.lcSize = (h + self._lcHeightOffset, w)
		self.entriesListID = wx.NewId()
		self.entriesList=wx.ListCtrl(self,self.entriesListID,style=wx.LC_REPORT|wx.LC_SINGLE_SEL, size =self.lcSize)
		for column in self.lcColumns:
			index = self.lcColumns.index(column)
			self.entriesList.InsertColumn(index,column[0],width=column[1])


		self.entriesList.Bind(wx.EVT_LIST_ITEM_FOCUSED, self.onListItemSelected)
		self.entriesList.Bind(wx.EVT_KEY_DOWN, self.onInputChar)
		entriesSizer.Add(self.entriesList, proportion= 3)
		settingsSizer.Add(entriesSizer)
		if self.tc1:
			tc1Sizer=wx.BoxSizer(wx.VERTICAL)
			label=wx.StaticText(self,-1,label=self.tc1["label"])
			tc1Sizer.Add(label)
			self.TC1 = wx.TextCtrl(self, wx.ID_ANY,style=wx.TE_MULTILINE | wx.TE_READONLY|wx.TE_RICH, size = self.tc1["size"])
			self.TC1.Bind(wx.EVT_KEY_DOWN, self.onInputChar)
			tc1Sizer.Add(self.TC1)
			settingsSizer.Add(tc1Sizer)
			
		if self.tc2:
			tc2Sizer=wx.BoxSizer(wx.VERTICAL)
			label=wx.StaticText(self,-1,label=self.tc2["label"])
			tc2Sizer.Add(label)
			self.TC2 = wx.TextCtrl(self, wx.ID_ANY,style=wx.TE_MULTILINE | wx.TE_READONLY|wx.TE_RICH, size = self.tc2["size"])
			self.TC2.Bind(wx.EVT_KEY_DOWN, self.onInputChar)
			tc2Sizer.Add(self.TC2)
			settingsSizer.Add(tc2Sizer)
		
		buttonsSizer=wx.BoxSizer(wx.HORIZONTAL)
		for button in self.buttons:
			button = wx.Button(self, button[0], label = button[1])
			button.Bind(wx.EVT_BUTTON,self.onButton)
			button.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
			buttonsSizer.Add(button)

		settingsSizer.Add(buttonsSizer)
		mainSizer.Add(settingsSizer,border=20,flag=wx.LEFT|wx.RIGHT|wx.TOP)

		closeButton = wx.Button(self, wx.ID_CLOSE, label = _("&Close"))
		closeButton.Bind(wx.EVT_BUTTON,self.onCloseButton)
		closeButton.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		mainSizer.Add(closeButton,border=20,flag=wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.CENTER)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		mainSizer.Fit(self)
		self.SetSizer(mainSizer)



		self.entriesList.SetFocus()
		self.refreshList()



	def onCloseButton(self, evt):
		self.Close()
		evt.Skip()

	def onClose(self, evt):
		self.alive = False
		if self.timer != None:
			self.timer.Stop()
			self.timer = None
		
		self.Destroy()
	def onButton(self, evt):
		id = evt.GetId()
		for button in self.buttons:
			if button[0] == id and button[2]is not None:
				button[2]()
				return





		evt.Skip()
		
	def onKeyDown(self, evt):
		key = evt.GetKeyCode()
		if (key == wx.WXK_ESCAPE):
			self.Close()
			return

		evt.Skip()
		
	def onInputChar(self, evt):
		id = evt.GetId()
		key = evt.GetKeyCode()
		if (key == wx.WXK_RETURN):
			self.goTo()
			return
		if (key == wx.WXK_SPACE):
			if self.tc2 and wx.GetKeyState(wx.WXK_CONTROL):
				text = self.TC2.GetValue()
			elif self.tc1:
				text = self.TC1.GetValue()
			wx.CallLater(30, speech.speakMessage, text)
			return

			return

		elif id == self.entriesListID and((key == wx.WXK_DELETE) or (key == wx.WXK_NUMPAD_DELETE)):
			if gui.messageBox(_("Are you sure you wish to delete this items?"), _("Deletion of items"), wx.YES_NO|wx.ICON_WARNING) != wx.YES: return
			self.delete()
			return
			
		elif (key == wx.WXK_ESCAPE):
			self.Close()
			return
		evt.Skip()


	def refreshList(self,activeIndex=0):
		self.entriesList.DeleteAllItems()
		self.collection = self.collectionObject.refreshItemsList()
		count = len(self.collection)
		if count == 0:
			self.Destroy()
			return
			
		for item in self.collection:
			self.entriesList.Append(self.get_lcColumnsDatas(item))
			

		index = activeIndex
		if activeIndex > count-1:
			index = count-1
		
		self.entriesList.Select(index)
		self.entriesList.SetItemState(index,wx.LIST_STATE_FOCUSED,wx.LIST_STATE_FOCUSED)
		item = self.collection[index]
		if self.tc1:
			self.TC1.Clear()
			self.TC1.AppendText(self.get_tc1Datas(item))
			self.TC1.SetInsertionPoint(0)
		if self.tc2:
			self.TC2.Clear()
			self.TC2.AppendText(self.get_tc2Datas(item))
			self.TC2.SetInsertionPoint(0)

		


	def onListItemSelected(self, evt):
		index=evt.GetIndex()
		item = self.collection[index]
		if self.tc1:
			self.TC1.Clear()
			text = self.get_tc1Datas(item)
			self.TC1.AppendText(text)
			self.TC1.SetInsertionPoint(0)
			if self.timer != None:
				self.timer.Stop()
			self.timer = core.callLater(800, ui.message, text)
		if self.tc2:
			self.TC2.Clear()
			self.TC2.AppendText(self.get_tc2Datas(item))
			self.TC2.SetInsertionPoint(0)
			
		evt.Skip()


		

	def goTo(self):
		printDebug ("ReportDialog goTo")
		index=self.entriesList.GetFocusedItem()
		self.collection[index].goTo()
		wx.CallAfter(self.parent.Close)
		self.Close()
		speech.cancelSpeech()
		oldSpeechMode = speech.speechMode
		speech.speechMode = speech.speechMode_off
		core.callLater(500, self.collectionObject.speakContext, oldSpeechMode)

	def delete(self):
		index=self.entriesList.GetFocusedItem()
		item= self.collection[index]
		self.collectionObject.delete(item)
		self.refreshList(index)
		if len(self.collection) == 0: return
		self.entriesList.SetFocus()
		time.sleep(0.1)
		api.processPendingEvents()
		obj  = api.getFocusObject()
		queueEvent("gainFocus",obj)


	def deleteAll(self):
		if gui.messageBox(_("Are you sure you wish to delete all items?"), _("Deletion of all items"), wx.YES_NO|wx.ICON_WARNING) != wx.YES: return
		self.collectionObject.deleteAll()
		self.Close()
	@classmethod
	def run(cls,  collectionObject, makeChoiceDialog):
		#gui.mainFrame.prePopup()
		d= cls(makeChoiceDialog, collectionObject)
		d.CenterOnScreen()
		d.ShowModal()
		#gui.mainFrame.postPopup()
	#run = classmethod(run)
