# globalPlugins\wordAccessEnhancement\ww_config.py
# A part of WordAccessEnhancement add-on
#Copyright (C) 2019 paulber19
#This file is covered by the GNU General Public License.


import addonHandler
addonHandler.initTranslation()
import appModuleHandler
from logHandler import log
import os
import globalVars
import sys
import gui
from gui.settingsDialogs import SettingsDialog, MultiCategorySettingsDialog, SettingsPanel
import wx
from configobj import ConfigObj, ConfigObjError
# ConfigObj 5.1.0 and later integrates validate module.
try:
	from configobj.validate import Validator, VdtTypeError
except ImportError:
	from validate import Validator, VdtTypeError, ConfigObjError

_curAddon = addonHandler.getCodeAddon()
path = os.path.join(_curAddon.path, "shared")
sys.path.append(path)
from ww_py3Compatibility import importStringIO, _unicode
from ww_utils import printDebug, InformationDialog
from ww_NVDAStrings  import NVDAString
from ww_addonConfigManager import _addonConfigManager
del sys.path[-1]

StringIO = importStringIO()
import characterProcessing
import speech
NVDASpeechSettings = ["autoLanguageSwitching", "autoDialectSwitching", "symbolLevel", "trustVoiceLanguage", "includeCLDR" ]
NVDASpeechManySettings = ["capPitchChange", "sayCapForCapitals", "beepForCapitals", "useSpellingFunctionality"]
SCT_Speech = "speech"
SCT_Many = "__many__"
class WordOptionsPanel(SettingsPanel):
	# Translators: This is the label for the notepadPlusPlus   settings  dialog.
	title = _("Options")
	
	def makeSettings(self, settingsSizer):

		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: This is the label for a group of editing options in the settings panel.
		groupText = _("Paragraph")
		group = gui.guiHelper.BoxSizerHelper(self, sizer=wx.StaticBoxSizer(wx.StaticBox(self, label=groupText), wx.VERTICAL))
		sHelper.addItem(group)
		# Translators: This is the label for a checkbox in the settings panel.
		labelText = _("&Skip empty paragraphs")
		self.skipEmptyParagraphBox = group.addItem(wx.CheckBox(self,wx.ID_ANY,label = labelText))
		self.skipEmptyParagraphBox.SetValue(_addonConfigManager.toggleSkipEmptyParagraphsOption(False))
		# Translators: This is the label for a checkbox in the settings panel.
		labelText = _("&Play sound when paragraph is skipped")
		self.playSoundOnSkippedParagraphBox = group.addItem(wx.CheckBox(self,wx.ID_ANY,label=_("&Play sound when paragraph is skipped")))
		self.playSoundOnSkippedParagraphBox.SetValue(_addonConfigManager.togglePlaySoundOnSkippedParagraphOption(False))
		# Translators: This is the label for a group of editing options in the settings panel.
		groupText = _("Automatic reading")
		group = gui.guiHelper.BoxSizerHelper(self, sizer=wx.StaticBoxSizer(wx.StaticBox(self, label=groupText), wx.VERTICAL))
		sHelper.addItem(group)
		# Translators: This is the label for a checkbox in the settings panel.
		labelText = _("&Activate automatic reading")
		self.automaticReadingCheckBox=group.addItem (wx.CheckBox(self,wx.ID_ANY, label= labelText))
		self.automaticReadingCheckBox.SetValue(_addonConfigManager.toggleAutomaticReadingOption(False))
		# Translators: This is the label for a checkbox in the settings panel.
		labelText = _("&Comments")
		self.autoCommentReadingCheckBox=group.addItem (wx.CheckBox(self,wx.ID_ANY, label= labelText))
		self.autoCommentReadingCheckBox.SetValue(_addonConfigManager.toggleAutoCommentReadingOption(False))
		# Translators: This is the label for a checkbox in the settings panel.
		labelText = _("&Footnotes")
		self.autoFootnoteReadingCheckBox=group.addItem (wx.CheckBox(self,wx.ID_ANY, label= labelText))
		self.autoFootnoteReadingCheckBox.SetValue(_addonConfigManager.toggleAutoFootnoteReadingOption(False))
		# Translators: This is the label for a checkbox in the settings panel.
		labelText = _("Read &with:")
		# Translators: choice labelsfor automatic reading.
		choice = [_("nothing"), _("a beep at start and end"), _("another voice")]
		self.autoReadingWithChoiceBox = group.addLabeledControl(labelText , wx.Choice, choices= choice)
		self.autoReadingWithChoiceBox.SetSelection(_addonConfigManager.getAutoReadingWithOption())
		# translators: label for a button in  Options settings panel.
		labelText = _("&Display voice's recorded setting")
		voiceInformationsButton= wx.Button(self, label=labelText)
		group.addItem (voiceInformationsButton)
		voiceInformationsButton.Bind(wx.EVT_BUTTON,self.onVoiceInformationButton)
		from versionInfo import version_year, version_major
		if  [version_year, version_major] < [2019,3]:
			# automatic reading is not available for nvda version less than nvda 2019.3
			for item in range(0, group.sizer.GetItemCount()):
				group.sizer.Hide(item)

	def onVoiceInformationButton(self, evt):
		def boolToText(val):
			return _("yes") if val else _("no")
		
		def punctuationLevelToText(level):
			return characterProcessing.SPEECH_SYMBOL_LEVEL_LABELS[int(level)]
		
		NVDASpeechSettingsInfos = [
			("Automatic language switching (when supported)", boolToText), 
			("Automatic dialect switching (when supported)", boolToText),
			("Punctuation/symbol level", punctuationLevelToText),
			("Trust voice's language when processing characters and symbols", boolToText),
			("Include Unicode Consortium data (including emoji) when processing characters and symbols", boolToText),
			]
		
		
		NVDASpeechManySettingsInfos = [
			("Capital pitch change percentage", None),
			("Say &cap before capitals", boolToText),
			("&Beep for capitals", boolToText),
			("Use &spelling functionality if supported", boolToText),
			]
		
		autoReadingSynth = _addonConfigManager.getAutoReadingSynthSettings()
		if autoReadingSynth is None:
			# Translators: message to user to report no automatic reading voice.
			speech.speakMessage(_("No voice recorded for automatic reading"))
			return
		autoReadingSynthName= autoReadingSynth.get("synthName")
		textList = []
		textList.append(_("Synthetizer: %s") %autoReadingSynthName)
		synthSpeechSettings = autoReadingSynth[SCT_Speech]
		synthDisplayInfos= autoReadingSynth["SynthDisplayInfos"]
		textList.append(_("Output device: %s")%synthSpeechSettings["outputDevice"])
		for i in synthDisplayInfos:
			item = synthDisplayInfos[i]
			textList.append("%s: %s" %(item[0], item[1]))

		for setting in NVDASpeechSettings:
			val = synthSpeechSettings [setting] 
			index = NVDASpeechSettings.index(setting)
			(name, f) = NVDASpeechSettingsInfos[index]
			if f is not None:
				val = f(val)
			name = NVDAString(name).replace("&", "")
			textList.append("%s: %s"%(name, val))
		for setting in NVDASpeechManySettings:
			val = synthSpeechSettings [SCT_Many] [setting]
			if setting in synthSpeechSettings:
				val = synthSpeechSettings[setting]
			else:
				val = synthSpeechSettings[SCT_Many ] [setting]
			index = NVDASpeechManySettings.index(setting)
			(name, f) = NVDASpeechManySettingsInfos[index]
			if f is not None:
				val = f(val)
			name = NVDAString(name).replace("&", "")
			textList.append("%s: %s"%(name, val))

		# Translators: this is the title of informationdialog box  to show voice profile informations.
		dialogTitle = _("Voice settings for automatic reading")
		infos = "\r\n".join(textList)
		InformationDialog.run (None, dialogTitle, infos)

	def postInit(self):
		self.skipEmptyParagraphBox .SetFocus()
	
	def saveSettingChanges (self):
		if self.skipEmptyParagraphBox.IsChecked() != _addonConfigManager.toggleSkipEmptyParagraphsOption(False):
			_addonConfigManager.toggleSkipEmptyParagraphsOption()
		if self.playSoundOnSkippedParagraphBox.IsChecked() != _addonConfigManager.togglePlaySoundOnSkippedParagraphOption(False):
			_addonConfigManager.togglePlaySoundOnSkippedParagraphOption()
		if self.automaticReadingCheckBox.IsChecked() != _addonConfigManager.toggleAutomaticReadingOption(False):
			_addonConfigManager.toggleAutomaticReadingOption()	
		if self.autoCommentReadingCheckBox.IsChecked() != _addonConfigManager.toggleAutoCommentReadingOption(False):
			_addonConfigManager.toggleAutoCommentReadingOption()
		if self.autoFootnoteReadingCheckBox.IsChecked() != _addonConfigManager.toggleAutoFootnoteReadingOption(False):
			_addonConfigManager.toggleAutoFootnoteReadingOption()
		_addonConfigManager.setAutoReadingWithOption(self.autoReadingWithChoiceBox .GetSelection())
	def onSave(self):
		self.saveSettingChanges()


class WordUpdatePanel(SettingsPanel):
	# Translators: This is the label for the Update panel.
	title = _("Update")
	
	def makeSettings(self, settingsSizer):
		sHelper = gui.guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		# Translators: This is the label for a checkbox in the  update settings panel.
		labelText = _("Automatically check for &updates ")
		self.autoCheckForUpdatesCheckBox=sHelper.addItem (wx.CheckBox(self,wx.ID_ANY, label= labelText))
		self.autoCheckForUpdatesCheckBox.SetValue(_addonConfigManager.toggleAutoUpdateCheck(False))
		# Translators: This is the label for a checkbox in the update settings panel.
		labelText = _("Update also release versions to &developpement versions")
		self.updateReleaseVersionsToDevVersionsCheckBox=sHelper.addItem (wx.CheckBox(self,wx.ID_ANY, label= labelText))
		self.updateReleaseVersionsToDevVersionsCheckBox.SetValue(_addonConfigManager.toggleUpdateReleaseVersionsToDevVersions     (False))
		# translators: label for a button in  update settings panel.
		labelText = _("&Check for update")
		checkForUpdateButton= wx.Button(self, label=labelText)
		sHelper.addItem (checkForUpdateButton)
		checkForUpdateButton.Bind(wx.EVT_BUTTON,self.onCheckForUpdate)

	
		
	def onCheckForUpdate(self, evt):
		from .updateHandler import addonUpdateCheck
		releaseToDevVersion = self.updateReleaseVersionsToDevVersionsCheckBox.IsChecked() # or toggleUpdateReleaseVersionsToDevVersionsGeneralOptions(False)
		wx.CallAfter(addonUpdateCheck, auto = False, releaseToDev =releaseToDevVersion  )
		self.Close()
	
	
	def saveSettingChanges (self):
		if self.autoCheckForUpdatesCheckBox.IsChecked() != _addonConfigManager .toggleAutoUpdateCheck(False):
			_addonConfigManager .toggleAutoUpdateCheck(True)
		if self.updateReleaseVersionsToDevVersionsCheckBox.IsChecked() != _addonConfigManager .toggleUpdateReleaseVersionsToDevVersions     (False):
			_addonConfigManager .toggleUpdateReleaseVersionsToDevVersions     (True)

	
	def postSave(self):
		pass


	def onSave(self):
		self.saveSettingChanges()

class AddonSettingsDialog(MultiCategorySettingsDialog):
	title = "%s -%s"%(_curAddon.manifest["summary"], _("Settings"))
	INITIAL_SIZE = (1000, 480)
	MIN_SIZE = (470, 240) # Min height required to show the OK, Cancel, Apply buttons
	
	categoryClasses=[
		WordOptionsPanel,
		WordUpdatePanel
		]
	
	def __init__(self, parent, initialCategory=None):
		curAddon = addonHandler.getCodeAddon()
		# Translators: title of add-on parameters dialog.
		dialogTitle = _("Settings")
		self.title = "%s - %s"%(curAddon.manifest["summary"], dialogTitle)
		super(AddonSettingsDialog,self).__init__(parent, initialCategory)
		