########################################################################
########################################################################
########################################################################
####                                                                ####
####    csBehavior v1.1                                                ####
####                                                                ####
####    A Python program that allows you to run                     ####
####    behavioral/stimulus experiments                             ####
####    with a Teensy (and related) microcontrollers.                 ####
####                                                                 ####
####    questions to --> Chris Deister - cdeister@brown.edu         ####
####                                                                 ####
####    contributors: Chris Deister, Sinda Fekir                    ####
####    Anything that is licenseable is                             ####    
####    governed by a MIT License found in the github directory.     ####
####                                                                ####
########################################################################
########################################################################
########################################################################

# todo: add ser tracker for piezo
# todo: add import dict button 
# todo: fix ordering of windows populated from dicts
# todo: black.white in dictionaries
# todo: change optical to DAC

from tkinter import *
import tkinter.filedialog as fd
from pathlib import Path
import serial
import numpy as np
import h5py
import os
import datetime
import time
import platform
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import socket
import sys
import pandas as pd
from scipy.stats import norm
import pygsheets
from Adafruit_IO import *
import configparser

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$$   Class Definitions   $$$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

'''
There are six (6) classes
1. csGUI
    tkinter GUI layout
2. csVariable
3. csHDF
4. csMQTT
5. csSerial
    connect, read, write over serial to/from Teensy
6. csPlot
    make data plot, update data plot
'''
class csGUI(object):
    
    # a) initialize
    def __init__(self,varDict,timingDict,visualDict,opticalDict):
        
        self.curFeeds=[]
        self.totalMQTTDataCount = 1
        self.curNotes = []
        self.useGUI=1
        self.darkMode=1
        
    # b) window generation
    def makeParentWindow(self,master,varDict,timingDict,visualDict,opticalDict):
        # make the window object
        self.master = master
        self.taskBar = Frame(self.master)
        self.master.title("csBehavior")
        if self.darkMode:
            self.taskBar.configure(background='black')

        # log the hostname
        mchString=socket.gethostname()
        varDict['hostName']=mchString.split('.')[0]

        # set the initial geometry variables
        col1_width=14
        col2_width=8
        startRow=0
        leftCol = 0
        rightCol = 1
        entryWidth = 8

        # button is

        self.dirPath_btn = Button(self.taskBar,text="set path",justify=LEFT,width=col1_width,\
            command=lambda: self.getPath(varDict,timingDict,visualDict,opticalDict))  
        self.dirPath_btn.grid(row=startRow+1,column=rightCol,sticky=W,padx=10)
        if self.darkMode:
            self.dirPath_btn.configure(foreground='white')
            self.dirPath_btn.configure(highlightbackground='black') 
            self.dirPath_btn.configure(fg='black')
            
        self.dirPath_label=Label(self.taskBar, text="Save Path:", justify=LEFT)
        self.dirPath_label.grid(row=startRow,column=leftCol,padx=0,sticky=W)
        if self.darkMode:
            self.dirPath_label.configure(foreground='white')
            self.dirPath_label.configure(background='black')  
            
        self.dirPath_TV=StringVar(self.taskBar)
        self.dirPath_TV.set(varDict['dirPath'])
        self.dirPath_entry=Entry(self.taskBar, width=22, textvariable=self.dirPath_TV)
        self.dirPath_entry.grid(row=startRow+1,column=leftCol,padx=0,columnspan=1,sticky=W)
        if self.darkMode:
            self.dirPath_entry.configure(foreground='white')
            self.dirPath_entry.configure(background='black')
            
        self.comPath_label=Label(self.taskBar, text="COM Port:", justify=LEFT)
        self.comPath_label.grid(row=startRow+2,column=leftCol,padx=0,sticky=W)
        if self.darkMode:
            self.comPath_label.configure(foreground='white')
            self.comPath_label.configure(background='black')
            
        self.comPath_TV=StringVar(self.taskBar)
        self.comPath_TV.set(varDict['comPath'])
        self.checkCOMPort(varDict)
        self.comPath_entry=Entry(self.taskBar, width=22, textvariable=self.comPath_TV)
        self.comPath_entry.grid(row=startRow+3,column=leftCol,padx=0,sticky=W)
        if self.darkMode:
            self.comPath_entry.configure(background='black')
            self.comPath_entry.configure(foreground='white')
            
        self.refreshCom_btn = Button(self.taskBar,text="guess com",justify=LEFT,\
            width=col1_width,command=lambda: self.checkCOMPort(varDict))
        self.refreshCom_btn.grid(row=startRow+startRow+3,column=rightCol,padx=10,sticky=W)
        self.refreshCom_btn['state'] = 'normal'
        if self.darkMode:
            self.refreshCom_btn.configure(foreground='white')
            self.refreshCom_btn.configure(highlightbackground='black')
            self.refreshCom_btn.configure(fg='black')
            
            
        self.blank=Label(self.taskBar, text=" ——————————————–––",justify=LEFT)
        self.blank.grid(row=startRow+4,column=leftCol,padx=0,sticky=W)
        if self.darkMode:
            self.blank.configure(background='black')
            self.blank.configure(foreground='white')
            
        self.subjID_label=Label(self.taskBar, text="Subject ID:", justify=LEFT)
        self.subjID_label.grid(row=startRow+5,column=0,padx=0,sticky=W)
        if self.darkMode:
            self.subjID_label.configure(background='black')
            self.subjID_label.configure(foreground='white')
            
        self.subjID_TV=StringVar(self.taskBar)
        self.subjID_TV.set(varDict['subjID'])
        self.subjID_entry=Entry(self.taskBar, width=entryWidth, textvariable=self.subjID_TV)
        self.subjID_entry.grid(row=startRow+5,column=leftCol,padx=0,sticky=E)
        if self.darkMode:
            self.subjID_entry.configure(background='black')
            self.subjID_entry.configure(foreground='white')
            
        self.teL=Label(self.taskBar, text="Total Trials:",justify=LEFT)
        self.teL.grid(row=startRow+6,column=0,padx=0,sticky=W)
        if self.darkMode:
            self.teL.configure(background='black')
            self.teL.configure(foreground='white')
            
        self.totalTrials_TV=StringVar(self.taskBar)
        self.totalTrials_TV.set(varDict['totalTrials'])
        self.totalTrials_entry = Entry(self.taskBar,width=entryWidth,textvariable=self.totalTrials_TV)
        self.totalTrials_entry.grid(row=startRow+6,column=leftCol,padx=0,sticky=E)
        if self.darkMode:
            self.totalTrials_entry.configure(background='black')
            self.totalTrials_entry.configure(foreground='white')
            
        self.teL=Label(self.taskBar, text="Current Session:",justify=LEFT)
        self.teL.grid(row=startRow+7,column=leftCol,padx=0,sticky=W)
        if self.darkMode:
            self.teL.configure(background='black')
            self.teL.configure(foreground='white')
            
        self.curSession_TV=StringVar(self.taskBar)
        self.curSession_TV.set(varDict['curSession'])
        self.te = Entry(self.taskBar,width=entryWidth,textvariable=self.curSession_TV)
        self.te.grid(row=startRow+7,column=leftCol,padx=0,sticky=E)
        if self.darkMode:
            self.te.configure(background='black')
            self.te.configure(foreground='white')
            
        self.blL=Label(self.taskBar, text=" ——————————————–––",justify=LEFT)
        self.blL.grid(row=startRow+8,column=leftCol,padx=0,sticky=W)
        if self.darkMode:
            self.blL.configure(background='black')
            self.blL.configure(foreground='white')
            
        self.plotSamps_label=Label(self.taskBar, text="Samps per Plot:", justify=LEFT)
        self.plotSamps_label.grid(row=startRow+9,column=0,padx=0,sticky=W)
        if self.darkMode:
            self.plotSamps_label.configure(background='black')
            self.plotSamps_label.configure(foreground='white')
            
        self.plotSamps_TV=StringVar(self.taskBar)
        self.plotSamps_TV.set(varDict['plotSamps'])
        self.plotSamps_entry=Entry(self.taskBar, width=10, textvariable=self.plotSamps_TV)
        self.plotSamps_entry.grid(row=startRow+9,column=0,padx=0,sticky=E)
        if self.darkMode:
            self.plotSamps_entry.configure(background='black')
            self.plotSamps_entry.configure(foreground='white')
            
        self.updateCount_label=Label(self.taskBar, text="Plot Update:", justify=LEFT)
        self.updateCount_label.grid(row=startRow+10,column=0,padx=0,sticky=W)
        if self.darkMode:
            self.updateCount_label.configure(background='black')
            self.updateCount_label.configure(foreground='white')
            
        self.updateCount_TV=StringVar(self.taskBar)
        self.updateCount_TV.set(varDict['updateCount'])
        self.updateCount_entry=Entry(self.taskBar, width=10, textvariable=self.updateCount_TV)
        self.updateCount_entry.grid(row=startRow+10,column=0,padx=0,sticky=E)
        if self.darkMode:
            self.updateCount_entry.configure(background='black')
            self.updateCount_entry.configure(foreground='white')

        self.lickAThr_label=Label(self.taskBar, text="Lick Thr:", justify=LEFT)
        self.lickAThr_label.grid(row=startRow+11,column=0,padx=0,sticky=W)
        if self.darkMode:
            self.lickAThr_label.configure(background='black')
            self.lickAThr_label.configure(foreground='white')
        self.lickAThr_TV=StringVar(self.taskBar)
        self.lickAThr_TV.set(varDict['lickAThr'])
        self.lickAThr_entry=Entry(self.taskBar, width=10, textvariable=self.lickAThr_TV)
        self.lickAThr_entry.grid(row=startRow+11,column=0,padx=0,sticky=E)
        if self.darkMode:
            self.lickAThr_entry.configure(background='black')
            self.lickAThr_entry.configure(foreground='white')

        self.shapingTrial_TV=IntVar()
        self.shapingTrial_TV.set(varDict['shapingTrial'])
        self.shapingTrial_Toggle=Checkbutton(self.taskBar,text="Shaping Trial",\
            variable=self.shapingTrial_TV,onvalue=1,offvalue=0)
        self.shapingTrial_Toggle.grid(row=startRow+13,column=0,pady=4,sticky=W)
        self.shapingTrial_Toggle.select()
        if self.darkMode:
            self.shapingTrial_Toggle.configure(foreground='white')
            self.shapingTrial_Toggle.configure(background='black')

        self.useFlybackOpto_TV=IntVar()
        self.useFlybackOpto_TV.set(varDict['useFlybackOpto'])
        self.useFlybackOpto_Toggle=Checkbutton(self.taskBar,text="Use Flyback Opto?",\
            variable=self.useFlybackOpto_TV,onvalue=1,offvalue=0)
        self.useFlybackOpto_Toggle.grid(row=startRow+14,column=0,sticky=W)
        self.useFlybackOpto_Toggle.select()
        if self.darkMode:
            self.useFlybackOpto_Toggle.configure(foreground='white')
            self.useFlybackOpto_Toggle.configure(background='black')

        self.chanPlot_label=Label(self.taskBar, text="Scope:", justify=LEFT)
        self.chanPlot_label.grid(row=startRow+5,column=rightCol,padx=10,sticky=W)
        if self.darkMode:
            self.chanPlot_label.configure(foreground='white')
            self.chanPlot_label.configure(background='black')

        self.chanPlotIV=IntVar()
        self.chanPlotIV.set(varDict['chanPlot'])
        if self.darkMode == 0:
            Radiobutton(self.taskBar, text="Load Cell", \
                variable=self.chanPlotIV, value=4).grid(row=startRow+6,column=rightCol,padx=10,pady=3,sticky=W,)
            Radiobutton(self.taskBar, text="Lick Sensor", \
                variable=self.chanPlotIV, value=5).grid(row=startRow+7,column=rightCol,padx=10,pady=3,sticky=W)
            Radiobutton(self.taskBar, text="Motion", \
                variable=self.chanPlotIV, value=6).grid(row=startRow+8,column=rightCol,padx=10,pady=3,sticky=W)
            Radiobutton(self.taskBar, text="DAC1", \
                variable=self.chanPlotIV, value=9).grid(row=startRow+9,column=rightCol,padx=10,pady=3,sticky=W)
            Radiobutton(self.taskBar, text="Thr Licks", \
                variable=self.chanPlotIV, value=11).grid(row=startRow+10,column=rightCol,padx=10,pady=3,sticky=W)
            Radiobutton(self.taskBar, text="Nothing", \
                variable=self.chanPlotIV, value=0).grid(row=startRow+11,column=rightCol,padx=10,pady=3,sticky=W)

        if self.darkMode:
            Radiobutton(self.taskBar, text="Load Cell", \
                variable=self.chanPlotIV, value=4,foreground='white',background='black').grid(row=startRow+6,column=rightCol,padx=10,pady=3,sticky=W,)
            Radiobutton(self.taskBar, text="Lick Sensor", \
                variable=self.chanPlotIV, value=5,foreground='white',background='black').grid(row=startRow+7,column=rightCol,padx=10,pady=3,sticky=W)
            Radiobutton(self.taskBar, text="Motion", \
                variable=self.chanPlotIV, value=6,foreground='white',background='black').grid(row=startRow+8,column=rightCol,padx=10,pady=3,sticky=W)
            Radiobutton(self.taskBar, text="DAC1", \
                variable=self.chanPlotIV, value=9,foreground='white',background='black').grid(row=startRow+9,column=rightCol,padx=10,pady=3,sticky=W)
            Radiobutton(self.taskBar, text="Thr Licks", \
                variable=self.chanPlotIV, value=11,foreground='white',background='black').grid(row=startRow+10,column=rightCol,padx=10,pady=3,sticky=W)
            Radiobutton(self.taskBar, text="Nothing", \
                variable=self.chanPlotIV, value=0,foreground='white',background='black').grid(row=startRow+11,column=rightCol,padx=10,pady=3,sticky=W)

        # MQTT Stuff
        self.blL=Label(self.taskBar, text="—— Notes ——————————",justify=LEFT)
        self.blL.grid(row=startRow+15,column=leftCol,padx=0,sticky=W)    
        if self.darkMode:
            self.blL.configure(foreground='white')
            self.blL.configure(background='black')    

        self.logMQTT_TV=IntVar()
        self.logMQTT_TV.set(varDict['chanPlot'])
        self.logMQTT_Toggle=Checkbutton(self.taskBar,text="Log MQTT Info?",\
            variable=self.logMQTT_TV,onvalue=1,offvalue=0)
        self.logMQTT_Toggle.grid(row=startRow+16,column=0,sticky=W)
        self.logMQTT_Toggle.select
        if self.darkMode:
            self.logMQTT_Toggle.configure(background='black')
            self.logMQTT_Toggle.configure(foreground='white')

        self.tBtn_detection = Button(self.taskBar,text="Task:Detection",justify=LEFT,\
            width=col1_width,command=self.do_detection)
        self.tBtn_detection.grid(row=startRow+20,column=leftCol,padx=10,sticky=W)
        self.tBtn_detection['state'] = 'disabled'
        if self.darkMode:
            self.tBtn_detection.configure(highlightbackground='black')
            self.tBtn_detection.configure(foreground='white')
            self.tBtn_detection.configure(fg='black')

        self.tBtn_trialOpto = Button(self.taskBar,text="Task:Trial Opto",justify=LEFT,width=col1_width,\
            command=self.do_trialOpto)
        self.tBtn_trialOpto.grid(row=startRow+21,column=leftCol,padx=10,sticky=W)
        self.tBtn_trialOpto['state'] = 'disabled'
        if self.darkMode:
            self.tBtn_trialOpto.configure(highlightbackground='black')
            self.tBtn_trialOpto.configure(foreground='white')
            self.tBtn_trialOpto.configure(fg='black')

        self.tBtn_simpleRecord = Button(self.taskBar,text="Task:Just Record",justify=LEFT,width=col1_width,\
            command=self.do_justRecord)
        self.tBtn_simpleRecord.grid(row=startRow+22,column=leftCol,padx=10,sticky=W)
        self.tBtn_simpleRecord['state'] = 'disabled'
        if self.darkMode:
            self.tBtn_simpleRecord.configure(highlightbackground='black')
            self.tBtn_simpleRecord.configure(foreground='white')
            self.tBtn_simpleRecord.configure(fg='black')

        self.hpL=Label(self.taskBar, text="Hash Path:",justify=LEFT)
        self.hpL.grid(row=startRow+17,column=0,padx=0,sticky=W)
        if self.darkMode:
            self.hpL.configure(background='black')
            self.hpL.configure(foreground='white')
        self.hashPath_TV=StringVar(self.taskBar)
        self.hashPath_TV.set(varDict['hashPath'])
        self.te = Entry(self.taskBar,width=11,textvariable=self.hashPath_TV)
        self.te.grid(row=startRow+17,column=0,padx=0,sticky=E)
        if self.darkMode:
            self.te.configure(background='black')
            self.te.configure(foreground='white')

        self.vpR=Label(self.taskBar, text="Vol/Rwd (~):",justify=LEFT)
        self.vpR.grid(row=startRow+18,column=0,padx=0,sticky=W)
        if self.darkMode:
            self.vpR.configure(background='black')
            self.vpR.configure(foreground='white')
        self.volPerRwd_TV=StringVar(self.taskBar)
        self.volPerRwd_TV.set(varDict['volPerRwd'])
        self.te = Entry(self.taskBar,width=11,textvariable=self.volPerRwd_TV)
        self.te.grid(row=startRow+18,column=0,padx=0,sticky=E)
        if self.darkMode:
            self.te.configure(background='black')
            self.te.configure(foreground='white')

        # self.stimButton = Button(self.taskBar,text="Dev:Stim",justify=LEFT,width=col1_width,\
        #     command= lambda: self.makePulseControl(varDict))
        # self.stimButton.grid(row=startRow+18,column=rightCol,padx=10,sticky=W)

        # options:
        self.quitButton = Button(self.taskBar,text="Quit",width=col1_width,\
            command=lambda: self.closeup(varDict,visualDict,timingDict,opticalDict))
        self.quitButton.grid(row=startRow+21,column=rightCol,padx=10,pady=5,sticky=W)
        if self.darkMode:
            self.quitButton.configure(foreground='white')
            self.quitButton.configure(highlightbackground='black')
            self.quitButton.configure(fg='black')

        self.devControlButton = Button(self.taskBar,text="Dev:Gen",justify=LEFT,width=col1_width,\
            command= lambda: self.makeDevControl(varDict))
        self.devControlButton.grid(row=startRow+14,column=1,padx=10,sticky=W)
        if self.darkMode:
            self.devControlButton.configure(highlightbackground='black')
            self.devControlButton.configure(foreground='white')
            self.devControlButton.configure(fg='black')
        
        self.tBtn_timeWin = Button(self.taskBar,text="Vars: Timing",justify=LEFT,width=col1_width,\
            command=lambda: self.makeTimingWindow(self,timingDict))
        self.tBtn_timeWin.grid(row=startRow+16,column=rightCol,padx=10,pady=5,sticky=W)
        if self.darkMode:
            self.tBtn_timeWin.configure(highlightbackground='black')
            self.tBtn_timeWin.configure(foreground='white')
            self.tBtn_timeWin.configure(fg='black')

        self.tBtn_visualWin = Button(self.taskBar,text="Vars: Sensory",justify=LEFT,width=col1_width,\
            command=lambda: self.makeVisualWindow(self,visualDict))
        self.tBtn_visualWin.grid(row=startRow+17,column=rightCol,padx=10,pady=2,sticky=W)
        if self.darkMode:
            self.tBtn_visualWin.configure(highlightbackground='black')
            self.tBtn_visualWin.configure(foreground='white')
            self.tBtn_visualWin.configure(fg='black')

        self.tBtn_opticalWin = Button(self.taskBar,text="Vars: Optical",justify=LEFT,width=col1_width,\
            command=lambda: self.makeOpticalWindow(self,opticalDict))
        self.tBtn_opticalWin.grid(row=startRow+18,column=rightCol,padx=10,pady=2,sticky=W)
        if self.darkMode:
            self.tBtn_opticalWin.configure(highlightbackground='black')
            self.tBtn_opticalWin.configure(foreground='white')
            self.tBtn_opticalWin.configure(fg='black')

        self.tBtn_mqttWin = Button(self.taskBar,text="MQTT Opts",justify=LEFT,width=col1_width,\
            command=lambda: self.makeMQTTWindow(varDict))
        self.tBtn_mqttWin.grid(row=startRow+19,column=rightCol,padx=10,pady=2,sticky=W)
        if self.darkMode:
            self.tBtn_mqttWin.configure(highlightbackground='black')
            self.tBtn_mqttWin.configure(foreground='white')
            self.tBtn_mqttWin.configure(fg='black')

        self.tBtn_notesWin = Button(self.taskBar,text="Notes",justify=LEFT,width=col1_width,\
            command=lambda: self.makeNotesWindow(varDict))
        self.tBtn_notesWin.grid(row=startRow+20,column=rightCol,padx=10,pady=2,sticky=W)
        if self.darkMode:
            self.tBtn_notesWin.configure(highlightbackground='black')
            self.tBtn_notesWin.configure(foreground='white')
            self.tBtn_notesWin.configure(fg='black')
        
        # Finish the window
        self.taskBar.pack(side=TOP, fill=X)

        # open the dev control window by default
        # self.makeDevControl(varDict)
        
    def populateVarFrameFromDict(self,dictName,stCol,varPerCol,headerString,frameName,excludeKeys=[],entryWidth=5):
        
        rowOffset = 2
        rowCounter = 0
        curColumn = stCol
        curColumnEnt = curColumn + 1

        if varPerCol == 0:
            varPerCol = len(list(dictName.keys()))
        if self.darkMode:
            exec('r_label = Label(self.{}, text="{}",background ="black",foreground ="white")'.format(frameName,headerString))
        else:
            exec('r_label = Label(self.{}, text="{}")'.format(frameName,headerString))
        exec('r_label.grid(row=1,column=stCol,sticky=W)'.format(dictName))
        
        for key in list(dictName.keys()):
            if key not in excludeKeys:
                
                exec('self.{}_TV=StringVar(self.{})'.format(key,frameName))
                if self.darkMode:
                    exec('self.{}_label = Label(self.{}, text="{}",background ="black",foreground ="white")'.format(key,frameName,key))
                    exec('self.{}_entries=Entry(self.{},width={},textvariable=self.{}_TV,background ="black",foreground ="white")'.format(key,frameName,entryWidth,key))
                elif self.darkMode==0:
                    exec('self.{}_label = Label(self.{}, text="{}")'.format(key,frameName,key))
                    exec('self.{}_entries=Entry(self.{},width={},textvariable=self.{}_TV)'.format(key,frameName,entryWidth,key))
                exec('self.{}_label.grid(row={}, column=curColumnEnt,sticky=W)'.format(key,rowCounter+rowOffset))
                exec('self.{}_entries.grid(row={}, column=curColumn)'.format(key,rowCounter+rowOffset))
                
                # This stuff lets us display ints, floats, ranges and lists correctly

                try:
                    if type(dictName[key]) is int or type(dictName[key]) is float:
                        exec('self.{}_TV.set({})'.format(key,dictName[key]))
                    elif type(dictName[key]) is range:
                        tempStr = ["{},>,{}".format(dictName[key][0],dictName[key][-1])]
                        exec('self.{}_TV.set({})'.format(key,tempStr))
                    elif type(dictName[key]) is list:
        
                        tempStr = ''
                        if len(dictName[key]) == 0:
                            pass
                        elif len(dictName[key]) > 0:
                            for x in dictName[key]:
                                tempStr = tempStr + '{}'.format(x) + ','
                            if tempStr[-1] is ',':
                                tempStr=tempStr[0:-1]
        
                        exec('self.{}_TV.set(tempStr)'.format(key))
                except:
                    exec('self.{}_TV.set("")'.format(key))
                    
                rowCounter=rowCounter+1
                
                if rowCounter >= varPerCol:
                    rowCounter = 0
                    curColumn = curColumn + 2
                    curColumnEnt = curColumn + 1
                    
    def makeTimingWindow(self,master,timingDict):
        
        self.timingControl_frame = Toplevel(self.master)
        if self.darkMode:
            self.timingControl_frame.configure(background='black')

        self.timingControl_frame.title('Session/Trial Timing')
        self.populateVarFrameFromDict(timingDict,0,0,'Current Values','timingControl_frame',['varsToUse','trialCount'],entryWidth=12)
        self.tBtn_updateTimingDict = Button(self.timingControl_frame,text="Update Timing Vars",justify=LEFT,width=15,\
            command=lambda: self.updateDictFromGUI(timingDict))
        if self.darkMode:
            self.tBtn_updateTimingDict.configure(foreground='white')
            self.tBtn_updateTimingDict.configure(highlightbackground='black')
            self.tBtn_updateTimingDict.configure(fg='black')
            
        self.tBtn_updateTimingDict.grid(row=999,column=0,padx=2,pady=2)
        
    def makeVisualWindow(self,master,visualDict):
        
        self.visualControl_frame = Toplevel(self.master)
        if self.darkMode:
            self.visualControl_frame.configure(background='black')
            
        self.visualControl_frame.title('Visual Probs')
        self.populateVarFrameFromDict(visualDict,0,10,'Cur Val','visualControl_frame',['varsToUse','trialCount'],entryWidth=12)
        self.tBtn_updateVisualDict = Button(self.visualControl_frame,text="Update Visual Vars",justify=LEFT,width=15,\
            command=lambda: self.updateDictFromGUI(visualDict))
        self.tBtn_updateVisualDict.grid(row=12,column=0,padx=2,pady=2)
        
    def makeOpticalWindow(self,master,opticalDict):
        
        self.opticalControl_frame = Toplevel(self.master)
        if self.darkMode:
            self.opticalControl_frame.configure(background='black')
            
        self.opticalControl_frame.title('Optical Probs')
        self.populateVarFrameFromDict(opticalDict,0,20,'Pew Pew','opticalControl_frame',['varsToUse','trialCount'],entryWidth=12)
        self.tBtn_updateOpticalDict = Button(self.opticalControl_frame,text="Update Optical Vars",justify=LEFT,width=15,\
            command=lambda: self.updateDictFromGUI(opticalDict))
        self.tBtn_updateOpticalDict.grid(row=22,column=0,padx=2,pady=2)
        
    def makeDevControl(self,varDict):
        
        dCBWd = 12
        self.deviceControl_frame = Toplevel(self.master)
        self.deviceControl_frame.title('Other Dev Control')
        self.weightOffsetBtn = Button(self.deviceControl_frame,text="Offset",width=dCBWd,\
            command=lambda: self.markOffset(varDict))
        self.weightOffsetBtn.grid(row=0,column=2)
        self.weightOffsetBtn['state'] = 'normal'
        self.offsetTV=StringVar(self.deviceControl_frame)
        self.offsetTV.set(varDict['loadBaseline'])
        self.offsetTV_Entry = Entry(self.deviceControl_frame,width=8,textvariable=self.offsetTV)
        self.offsetTV_Entry.grid(row=0,column=3)
        self.commandTV=StringVar(self.deviceControl_frame)
        self.commandTV.set("a1>")
        self.commandTV_Entry = Entry(self.deviceControl_frame,width=8,textvariable=self.commandTV)
        self.commandTV_Entry.grid(row=1,column=3)
        self.commandBtn = Button(self.deviceControl_frame,text="Command",width=dCBWd,\
            command=lambda: self.commandTeensy(varDict,self.commandTV.get()))
        self.commandBtn.grid(row=1,column=2)
        self.commandBtn['state'] = 'normal'
        self.flybackDurTV=StringVar(self.deviceControl_frame)
        self.flybackDurTV.set("25")
        self.flybackDurTV_Entry = Entry(self.deviceControl_frame,width=8,textvariable=self.flybackDurTV)
        self.flybackDurTV_Entry.grid(row=2,column=3)
        self.flybackDur_Btn = Button(self.deviceControl_frame,text="Fly Dur (us)",width=dCBWd,\
            command=lambda: self.commandTeensy(varDict,"q{}".format(int(self.flybackDurTV.get()))))
        self.flybackDur_Btn.grid(row=2,column=2)
        self.flybackDur_Btn['state'] = 'normal'
        self.testRewardBtn = Button(self.deviceControl_frame,text="Rwd",width=dCBWd,\
            command=lambda: self.commandTeensy(varDict,"z27>"))
        self.testRewardBtn.grid(row=0,column=0)
        self.testRewardBtn['state'] = 'normal'
        self.triggerBtn = Button(self.deviceControl_frame,text="Trig",width=dCBWd,\
            command=lambda: self.commandTeensy(varDict,"z25>"))
        self.triggerBtn.grid(row=0,column=1)
        self.triggerBtn['state'] = 'normal'

        # ******* Neopixel Stuff
        self.pDur_label = Label(self.deviceControl_frame,text="Neopixels:",justify=LEFT)
        self.pDur_label.grid(row=1, column=0)

        self.whiteLightBtn = Button(self.deviceControl_frame,text="NP:White",width=dCBWd,\
            command=lambda: self.commandTeensy(varDict,"n2>"))
        self.whiteLightBtn.grid(row=2,column=0)
        self.whiteLightBtn['state'] = 'normal'
        self.clearLightBtn = Button(self.deviceControl_frame,text="NP:Clear",width=dCBWd,\
            command=lambda: self.commandTeensy(varDict,"n1>")) 
        self.clearLightBtn.grid(row=2,column=1)
        self.clearLightBtn['state'] = 'normal'
        self.redLightBtn = Button(self.deviceControl_frame,text="NP:Red",width=dCBWd,\
            command=lambda: self.commandTeensy(varDict,"n3>")) 
        self.redLightBtn.grid(row=3,column=0)
        self.redLightBtn['state'] = 'normal'
        self.greenLightBtn = Button(self.deviceControl_frame,text="NP:Green",width=dCBWd,\
            command=lambda: self.commandTeensy(varDict,"n4>")) 
        self.greenLightBtn.grid(row=3,column=1)
        self.greenLightBtn['state'] = 'normal'
        self.greenLightBtn = Button(self.deviceControl_frame,text="NP:Blue",width=dCBWd,\
            command=lambda: self.commandTeensy(varDict,"n5>")) 
        self.greenLightBtn.grid(row=4,column=0)
        self.greenLightBtn['state'] = 'normal'
        self.greenLightBtn = Button(self.deviceControl_frame,text="NP:Purp",width=dCBWd,\
            command=lambda: self.commandTeensy(varDict,"n6>")) 
        self.greenLightBtn.grid(row=4,column=1)
        self.greenLightBtn['state'] = 'normal'
        self.incBrightnessBtn = Button(self.deviceControl_frame,text="NP: +",width=dCBWd,\
            command=lambda: self.deltaTeensy(varDict,'b',10))
        self.incBrightnessBtn.grid(row=5,column=0)
        self.incBrightnessBtn['state'] = 'normal'
        self.decBrightnessBtn = Button(self.deviceControl_frame,text="NP: -",width=dCBWd,\
            command=lambda: self.deltaTeensy(varDict,'b',-10))
        self.decBrightnessBtn.grid(row=5,column=1)
        self.decBrightnessBtn['state'] = 'normal'
        
    def makePulseControl(self,varDict):

        self.dC_Pulse = Toplevel(self.master)
        self.dC_Pulse.title('Stim Control')

        self.ramp1DurTV=StringVar(self.dC_Pulse)
        self.ramp1DurTV.set(int(varDict['ramp1Dur']))
        self.ramp1AmpTV=StringVar(self.dC_Pulse)
        self.ramp1AmpTV.set(int(varDict['ramp1Amp']))
        self.ramp2DurTV=StringVar(self.dC_Pulse)
        self.ramp2DurTV.set(int(varDict['ramp2Dur']))
        self.ramp2AmpTV=StringVar(self.dC_Pulse)
        self.ramp2AmpTV.set(int(varDict['ramp1Amp']))

        dCBWd = 12
        ptst=0
        
        self.pDur_label = Label(self.dC_Pulse,text="Dur (ms):",justify=LEFT)
        self.pDur_label.grid(row=0, column=ptst+2)
        self.amplitude_label = Label(self.dC_Pulse,text="Amp:",justify=LEFT)
        self.amplitude_label.grid(row=0, column=ptst+3)
        self.pulseTrainDac1Btn = Button(self.dC_Pulse,text="Pulses DAC1",width=dCBWd,\
            command=lambda: self.rampTeensyChan(varDict,int(self.ramp1AmpTV.get()),\
                int(self.ramp1DurTV.get()),90,10,1,0))
        self.pulseTrainDac1Btn.grid(row=1,column=ptst)
        self.pulseTrainDac1Btn['state'] = 'normal'
        self.rampDAC1Btn = Button(self.dC_Pulse,text="Ramp DAC1",width=dCBWd,\
            command=lambda: self.rampTeensyChan(int(self.ramp1AmpTV.get()),\
                int(self.ramp1DurTV.get()),100,1,1,1)) 
        self.rampDAC1Btn.grid(row=1,column=ptst+1)
        self.rampDAC1Btn['state'] = 'normal'
        self.ramp1DurTV_Entry = Entry(self.dC_Pulse,width=8,textvariable=self.ramp1DurTV)
        self.ramp1DurTV_Entry.grid(row=1,column=ptst+2)
        self.ramp1AmpTV_Entry = Entry(self.dC_Pulse,width=8,textvariable=self.ramp1AmpTV)
        self.ramp1AmpTV_Entry.grid(row=1,column=ptst+3)
        self.pulseTrainDac2Btn = Button(self.dC_Pulse,text="Pulses DAC2",width=dCBWd,\
            command=lambda: self.rampTeensyChan(int(self.ramp2AmpTV.get()),int(self.ramp2DurTV.get()),90,10,2,0)) 
        self.pulseTrainDac2Btn.grid(row=2,column=ptst)
        self.pulseTrainDac2Btn['state'] = 'normal'
        self.rampDAC2Btn = Button(self.dC_Pulse,text="Ramp DAC2",width=dCBWd,\
            command=lambda: rampTeensyChan(int(self.ramp2AmpTV.get()),int(self.ramp2DurTV.get()),100,1,2,1)) 
        self.rampDAC2Btn.grid(row=2,column=ptst+1)
        self.rampDAC2Btn['state'] = 'normal'
        self.ramp2DurTV_Entry = Entry(self.dC_Pulse,width=8,textvariable=self.ramp2DurTV)
        self.ramp2DurTV_Entry.grid(row=2,column=ptst+2)
        self.ramp2AmpTV_Entry = Entry(self.dC_Pulse,width=8,textvariable=self.ramp2AmpTV)
        self.ramp2AmpTV_Entry.grid(row=2,column=ptst+3)
        
    def makeDetectionOptions(self,varDict,timingDict,visualDict,opticalDict):
        
        startRow=startRow+1
        self.lickAThr_label=Label(self.taskBar, text="Lick Thresh:", justify=LEFT)
        self.lickAThr_label.grid(row=startRow,column=0,padx=0,sticky=W)
        self.lickAThr_TV=StringVar(self.taskBar)
        self.lickAThr_TV.set(varDict['lickAThr'])
        self.lickAThr_entry=Entry(self.taskBar, width=10, textvariable=self.lickAThr_TV)
        self.lickAThr_entry.grid(row=startRow,column=0,padx=0,sticky=E)
        self.lickAThr_entry.configure(background='black')
        self.lickAThr_entry.configure(foreground='white')

    def makeTrialOptoOptions(self,varDict,timingDict,visualDict,opticalDict):

        startRow=startRow+1
        self.pulsefrequency_label=Label(self.taskBar, text="Pulse Frequency:", justify=LEFT)
        self.pulsefrequency_label.grid(row=startRow,column=0,padx=0,sticky=W)
        self.pulsefrequency_TV=StringVar(self.taskBar)
        self.pulsefrequency_TV.set(varDict['pulsefrequency'])
        self.pulsefrequency_entry=Entry(self.taskBar, width=10, textvariable=self.pulsefrequency_TV)
        self.pulsefrequency_entry.grid(row=startRow,column=0,padx=0,sticky=E) 

        startRow=startRow+1
        self.pulsedutycycle_label=Label(self.taskBar, text="Pulse Duty Cycle:", justify=LEFT)
        self.pulsedutycycle_label.grid(row=startRow,column=0,padx=0,sticky=W)
        self.pulsedutycycle_TV=StringVar(self.taskBar)
        self.pulsedutycycle_TV.set(varDict['pulsedutycycle'])
        self.pulsedutycycle_entry=Entry(self.taskBar, width=10, textvariable=self.pulsedutycycle_TV)
        self.pulsedutycycle_entry.grid(row=startRow,column=0,padx=0,sticky=E) 

        startRow=startRow+1
        self.firstTrialWait_label=Label(self.taskBar, text="First Trial Wait:", justify=LEFT)
        self.firstTrialWait_label.grid(row=startRow,column=0,padx=0,sticky=W)
        self.firstTrialWait_TV=StringVar(self.taskBar)
        self.firstTrialWait_TV.set(varDict['firstTrialWait'])
        self.firstTrialWait_entry=Entry(self.taskBar, width=10, textvariable=self.firstTrialWait_TV)
        self.firstTrialWait_entry.grid(row=startRow,column=0,padx=0,sticky=E) 
        
    def makeMQTTWindow(self,varDict):
        dCBWd = 12
        hashPath = varDict['hashPath'] + '/simpHashes/csIO.txt'
        self.mqttControl_frame = Toplevel(self.master)
        self.mqttControl_frame.title('MQTT Feeds')

        self.getFeedsBtn = Button(self.mqttControl_frame,text="Get Feeds",width=dCBWd,\
            command=lambda:self.getFeeds(hashPath))
        self.getFeedsBtn.grid(row=0,column=0,sticky=W,pady=5,padx=5)
        self.getFeedsBtn['state'] = 'normal'

        self.feed_listbox = Listbox(self.mqttControl_frame,height=5)
        self.feed_listbox.grid(row=1,column=0,pady=5,rowspan=5,columnspan=2)

        self.mqttDataPointLab = Label(self.mqttControl_frame, text="Last Val:", justify=LEFT)
        self.mqttDataPointLab.grid(row=0,column=2,sticky=W)
        self.mqttDataPoint_TV = StringVar(self.mqttControl_frame)
        self.feedData_entry = Entry(self.mqttControl_frame,textvariable=self.mqttDataPoint_TV,width=10)
        self.feedData_entry.grid(row=0,column=3,padx=3)

        self.mqttDateStampLab = Label(self.mqttControl_frame, text="Date:", justify=LEFT)
        self.mqttDateStampLab.grid(row=1,column=2,sticky=W)
        self.mqttDateStamp_TV = StringVar(self.mqttControl_frame)
        self.mqttDateStamp_entry = Entry(self.mqttControl_frame,textvariable=self.mqttDateStamp_TV,width=10)
        self.mqttDateStamp_entry.grid(row=1,column=3,padx=3)

        self.mqttTimeStampLab = Label(self.mqttControl_frame, text="Time:", justify=LEFT)
        self.mqttTimeStampLab.grid(row=2,column=2,sticky=W)
        self.mqttTimeStamp_TV = StringVar(self.mqttControl_frame)
        self.mqttTimeStamp_entry = Entry(self.mqttControl_frame,textvariable=self.mqttTimeStamp_TV,width=10)
        self.mqttTimeStamp_entry.grid(row=2,column=3,padx=3)

        self.mqttDataCountLab = Label(self.mqttControl_frame, text="Count:", justify=LEFT)
        self.mqttDataCountLab.grid(row=3,column=2,sticky=W)
        self.mqttDataCount_TV = StringVar(self.mqttControl_frame)
        self.mqttDataCount_TV.set(self.totalMQTTDataCount)
        self.mqttDataCount_entry = Entry(self.mqttControl_frame,textvariable=self.mqttDataCount_TV,width=10)
        self.mqttDataCount_entry.grid(row=3,column=3,padx=3)

        self.inspectFeedsBtn = Button(self.mqttControl_frame,text="Inspect",width=dCBWd,\
            command=lambda:self.inspectFeed())
        self.inspectFeedsBtn.grid(row=6,column=0,sticky=W,pady=2,padx=2)
        self.inspectFeedsBtn['state'] = 'disabled'

        self.getAllDataBtn = Button(self.mqttControl_frame,text="Poll All",width=dCBWd,\
            command=lambda:self.getAllFeedData())
        self.getAllDataBtn.grid(row=7,column=0,sticky=W,pady=2,padx=2)
        self.getAllDataBtn['state'] = 'disabled'

        self.buAllDataBtn = Button(self.mqttControl_frame,text="Save Data",width=dCBWd,\
            command=lambda:self.allMQTTDataToPandas(varDict['dirPath']))
        self.buAllDataBtn.grid(row=7,column=1,sticky=W,pady=2,padx=2)
        self.buAllDataBtn['state'] = 'disabled'

        self.makeRigFeedBtn = Button(self.mqttControl_frame,text="+ Rig Feed",width=dCBWd,\
            command=lambda:self.makeRigFeed('rig-' + varDict['hostName']))
        self.makeRigFeedBtn.grid(row=8,column=1,sticky=W,pady=2,padx=2)
        self.makeRigFeedBtn['state'] = 'disabled'

        self.makeSubjFeedBtn = Button(self.mqttControl_frame,text="+ Subj Feeds",width=dCBWd,\
            command=lambda:csMQTT.makeSubjectFeeds(self,self.subjID_TV.get(),self.aio))
        self.makeSubjFeedBtn.grid(row=8,column=0,sticky=W,pady=2,padx=2)
        self.makeSubjFeedBtn['state'] = 'disabled'
        
    def makeNotesWindow(self,varDict):

        self.notes_frame = Toplevel(self.master)
        self.notes_frame.title('MQTT Feeds')
        
        self.noteEntry_TV = StringVar(self.notes_frame)
        self.noteEntry_TV.set('')
        self.noteEntry_entry = Entry(self.notes_frame,textvariable=self.noteEntry_TV,width=30)
        self.noteEntry_entry.grid(row=0,column=0,padx=3,rowspan=10,columnspan=4)

        self.sendNoteBtn = Button(self.notes_frame,text="log note",width=12,\
            command=lambda:self.makeNotes(self.subjID_TV.get().lower() + '-notes',self.noteEntry_TV.get(),varDict))
        self.sendNoteBtn.grid(row=11,column=0,sticky=W,pady=2,padx=2)
        self.sendNoteBtn['state'] = 'normal'
                
    # c) Methods
    def makeNotes(self,feedName,newNote,varDict):
        if self.logMQTT_TV.get()==1:
            try:
                self.aio
            except:
                self.aio = csMQTT.connect_REST(self,varDict['hashPath'] + '/simpHashes/csIO.txt')

        # always append to the note record
        self.curNotes.append(newNote)
        # we want a local copy and a remote copy (if we can)
        if self.logMQTT_TV.get()==1 and varDict['sessionOn']==0:
            csMQTT.sendData(self,feedName,newNote,self.aio)
        self.noteEntry_TV.set('')
        return self.curNotes

    def checkCOMPort(self,varDict):
        tempPath = self.guessComPort()
        if len(tempPath)>1:
            varDict['comPath'] = tempPath
            self.comPath_TV.set(tempPath)
        return varDict
    
    def getFeeds(self,hashPath):
        try:
            self.aio = csMQTT.connect_REST(self,hashPath)
            self.curFeeds = csMQTT.getMQTTFeeds(self,hashPath,self.aio)
            for thing in self.curFeeds:
                self.feed_listbox.insert(END, thing)
            self.buAllDataBtn['state'] = 'normal'
            self.getAllDataBtn['state'] = 'normal'
            self.inspectFeedsBtn['state'] = 'normal'
            self.makeRigFeedBtn['state'] = 'normal'
            self.makeSubjFeedBtn['state'] = 'normal'
        except:
            print("mqtt: couldn't load feeds")
            self.curFeeds = []
        return self.curFeeds,self.aio
    
    def inspectFeed(self):
        bb=[]
        curSelFeed = self.feed_listbox.curselection()
        aa= self.feed_listbox.get(curSelFeed)
        bb=csMQTT.getMQTTLast(self,aa.lower(),self.aio)
        try:
            self.mqttDataPoint_TV.set(bb.value)
            tsSp=bb.created_at.split('T')
            self.mqttDateStamp_TV.set(tsSp[0])
            self.mqttTimeStamp_TV.set(tsSp[1])
        except:
            self.mqttDataPoint_TV.set(bb)
            self.mqttDateStamp_TV.set([])
            self.mqttTimeStamp_TV.set([])
            
    def makeRigFeed(self,hostNameStr):
        csMQTT.makeMQTTFeed(self,hostNameStr,self.aio)
        
    def getAllFeedData(self):
        try:
            curSelFeed = self.feed_listbox.curselection()
            aa= self.feed_listbox.get(curSelFeed)
            bb=csMQTT.getMQTTDataAll(self,aa.lower(),self.aio)
            bbValues = []
            for x in bb:
                tVal = self.inferType(x.value)
                bbValues.append(tVal)
            self.totalMQTTDataCount = len(bbValues)
        except:
            self.totalMQTTDataCount=0
        self.mqttDataCount_TV.set(self.totalMQTTDataCount)
        bbFig = plt.figure(976)
        plt.plot(bbValues)
        plt.show(block=False)
        return self.totalMQTTDataCount,bbValues
    
    def allMQTTDataToPandas(self,savePath):
        
        curSelFeed = self.feed_listbox.curselection()
        aa= self.feed_listbox.get(curSelFeed)
        allData=csMQTT.getMQTTDataAll(self,aa.lower(),self.aio)
        tdStamp=datetime.datetime.now().strftime("%Y%m%d%H%M%S")

        tCreated_ats=[]
        tDates=[]
        tTimes=[]
        tIDs = []
        tValues=[]
        tFeedNames = []
        
        for x in allData:
            tCreated_ats.append(x.created_at)
            tS=x.created_at.split('T')
            tDates.append(tS[0])
            tTimes.append(tS[1])
            tIDs.append(x.id)
            tValues.append(self.inferType(x.value))
            tFeedNames.append(aa)

        self.mqttDataCount_TV.set(len(tIDs))
        tempArray = [tFeedNames,tCreated_ats,tDates,tTimes,tIDs,tValues]
        varIndex = ['feed_name','created_at','date','time','id','value']
        tempArray=list(list(zip(*tempArray)))
        newDF = pd.DataFrame(tempArray,columns = varIndex)
        csvPath = savePath + '/' +'{}_{}.csv'.format(aa,tdStamp)
        newDF.to_csv(csvPath)
        
        tCreated_ats=[]
        tDates=[]
        tTimes=[]
        tIDs = []
        tValues=[]
        tFeedNames = []
        
    def guessComPort(self):
        cp = platform.system()
        # if mac then teensy devices will be a cu.usbmodemXXXXX in /dev/ where XXXXX is the serial
        # if arm linux, then the teensy is most likely /dev/ttyACM0
        # if windows it will be some random COM.
        self.comPath=''
        if cp == 'Darwin':
            try: 
                devNames = self.checkForDevicesUnix('cu.u')
                self.comPath='/dev/' + devNames[0]
            except:
                pass
        elif cp == 'Windows':
            self.comPath='COM3'

        elif cp == 'Linux':
            self.comPath='/dev/ttyACM0'

        return self.comPath
    
    def checkForDevicesUnix(self,startString):
        dpth=Path('/dev')
        devPathStrings = []
        for child in dpth.iterdir():
            if startString in child.name:
                devPathStrings.append(child.name)
        self.devPathStrings = devPathStrings
        return self.devPathStrings
    
    def loadCSVDictionary(self,varDict,csvPath):
        try:
            tempMeta=pd.read_csv(csvPath,index_col=0,header=None)
            varDict = self.updateDictFromPandas(tempMeta,varDict)
            self.refreshGuiFromDict(varDict)
        except:
            pass
        return varDict
    
    def getPath(self,varDict,timingDict,visualDict,opticalDict):
        try:
            tPth = fd.askdirectory(title ="what what?")
            basePath = Path(tPth)
        except:
            # default to home directory
            basePath=Path(str(Path.home()))

        self.dirPath_TV.set(basePath.as_posix())
        self.subjID_TV.set(os.path.basename(basePath))
        varDict['dirPath']=basePath
        varDict['subjID']=basePath.name
        self.toggleTaskButtons(1)
        varDict = self.loadCSVDictionary(varDict,basePath.joinpath('sesVars.csv'))
        timingDict = self.loadCSVDictionary(timingDict,basePath.joinpath('timingVars.csv'))
        visualDict = self.loadCSVDictionary(visualDict,basePath.joinpath('sensVars.csv'))
        opticalDict = self.loadCSVDictionary(opticalDict,basePath.joinpath('opticalVars.csv'))

    def toggleTaskButtons(self,boolState=1):
        if boolState == 1:
            self.tBtn_trialOpto['state'] = 'normal'
            self.tBtn_detection['state'] = 'normal'
            self.tBtn_simpleRecord['state'] = 'normal'
        elif boolState == 0:
            self.tBtn_trialOpto['state'] = 'disabled'
            self.tBtn_detection['state'] = 'disabled'
            self.tBtn_simpleRecord['state'] = 'disabled'

    def inferType(self,singleCharNum):
        try:
            # if it is numeric, it can be a float
            singleCharNum = float(singleCharNum)
            # but it may be an int ...
            if singleCharNum.is_integer():
                singleCharNum = int(singleCharNum)
        except:
            # keep it as is, because it is empty or a char/string
            pass
        return singleCharNum
    
    def updateDictFromPandas(self,pandasSeries,targetDict):
        for x in range(0,len(pandasSeries)):
            varKey=pandasSeries.iloc[x].name
            a=pandasSeries.iloc[x][1]
            try:
                exec("targetDict['{}']=".format(varKey) + a)
            except:
                try:
                    targetDict[varKey]=a
                except:
                    pass
        return targetDict
    
    def updateDictFromGUI(self,targetDict,excludeKeys=['varsToUse']):
        for key in list(targetDict.keys()):
            if key not in excludeKeys:
                try:
                    a=eval('self.{}_TV.get()'.format(key))
                    a = a.split(',')
                    # if '/' or ',' is in the variable; 
                    # it's one of the step formats
                    if ':' in a or '/' in a:
                        a[1] = self.inferType(a[1])
                        tempList = [a[0],a[1]]
                        targetDict[key]=tempList

                    else:
                        tempList = []
                        if len(a)>1:
                            for n in a:
                                n= self.inferType(n)
                                tempList.append(n)
                                targetDict[key]=tempList
                        else:
                            a[0]= self.inferType(a[0])
                            targetDict[key]=a[0]
                except:
                    try:
                        a=eval('self.{}_TV.get()'.format(key))
                    except:
                        pass
                    
        return targetDict
    
    def updateDictFromTXT(self,varDict,configF):
        for key in list(varDict.keys()):
            try:
                a = config['sesVars'][{}.format(key)]
                try:
                    a=float(a)
                    if a.is_integer():
                        a=int(a)
                    exec('varDict["{}"]={}'.format(key,a))
                except:
                    exec('varDict["{}"]="{}"'.format(key,a))
            except:
                pass
        return varDict
    
    def updateTiming(self,timingDict):
        timingDict['trialLength']=int(self.maxTrialsTV.get())
        timingDict['trialTime_min']=int(self.minISI_TV.get())
        timingDict['trialTime_max']=int(self.maxISI_TV.get())
        timingDict['noLickTime_min']=int(self.minNoLick_TV.get())
        timingDict['noLickTime_max']=int(self.maxNoLick_TV.get())
        timingDict['trialTime_steps']=np.arange(timingDict['trialTime_min'],timingDict['trialTime_max'])
        timingDict['noLickTime_steps']=np.arange(timingDict['noLickTime_min'],timingDict['noLickTime_max'])
        return timingDict
    
    def dictToPandas(self,varDict,excludeKeys=['varsToUse']):
        curKey=[]
        curVal=[]
        for key in list(varDict.keys()):
            if key not in excludeKeys:
                curKey.append(key)
                curVal.append(varDict[key])
                self.pdReturn=pd.Series(curVal,index=curKey)
        return self.pdReturn
    
    def refreshPandas(self,varDict,visualDict,timingDict,opticalDict):
        try:
            self.updateDictFromGUI(varDict)
            self.updateDictFromGUI(visualDict)
            self.updateDictFromGUI(timingDict)
            self.updateDictFromGUI(opticalDict) 
        except:
            pass

        try:
            tbd=self.dictToPandas(varDict)
            tbd.to_csv(varDict['dirPath'] + '/' +'sesVars.csv')
            self.refreshGuiFromDict(varDict)
            
            tbd=self.dictToPandas(visualDict)
            tbd.to_csv(varDict['dirPath'] + '/' +'sensVars.csv')
            self.refreshGuiFromDict(visualDict)
            
            tbd=self.dictToPandas(opticalDict)
            tbd.to_csv(varDict['dirPath'] + '/' +'opticalVars.csv')
            self.refreshGuiFromDict(opticalDict)
            
            tbd=self.dictToPandas(timingDict)
            tbd.to_csv(varDict['dirPath'] + '/' +'timingVars.csv')
            self.refreshGuiFromDict(timingDict)
    
        except:
            pass
        
        return varDict,visualDict,timingDict,opticalDict    
    
    def refreshGuiFromDict(self,targetDict):
        for key in list(targetDict.keys()):
            try:
                eval('self.{}_TV.set(targetDict["{}"])'.format(key,key))
            except:
                pass
            
    def closeup(self,varDict,visualDict,timingDict,opticalDict,guiBool=1):
        self.toggleTaskButtons(1)
        self.tBtn_detection
        self.refreshPandas(varDict,visualDict,timingDict,opticalDict)

        try:
            varDict['sessionOn']=0
        except:
            varDict['canQuit']=1
            quitButton['text']="Quit"

        try:
            os.remove(varDict['dirPath'] + '/' + 'sesDataMemMap.npy')
        except:
            pass
        
        if varDict['canQuit']==1:
            # try to close a plot and exit    
            try:
                plt.close(varDict['detectPlotNum'])
                os._exit(1)
            # else exit
            except:
                os._exit(1)
                
    def commandTeensy(self,varDict,commandStr):
        varDict['comPath']=self.comPath_TV.get()
        try:
            teensy=csSer.connectComObj(varDict['comPath'],varDict['baudRate_teensy'])
            teensy.write("{}".format(commandStr).encode('utf-8'))
        except:
            print("couldn't connect check serial path")

        if '<' in commandStr:
            time.sleep(0.1)
            [tString,dNew]=self.readSerialVariable(teensy)
            if dNew:
                print('{} = {}'.format(commandStr[0],int(tString[2])))
            elif dNew==0:
                print("¯\_(ツ)_/¯ try again?")

        teensy.close()
        
        return varDict
    
    def readSerialVariable(self,comObj):
        sR=[]
        newData=0
        bytesAvail=comObj.inWaiting()

        if bytesAvail>0:
            sR=comObj.readline().strip().decode()
            sR=sR.split(',')
            if len(sR)==4 and sR[0]=='echo':
                newData=1

        self.sR=sR
        self.newData=newData
        self.bytesAvail = bytesAvail
        return self.sR,self.newData
    
    def deltaTeensy(self,varDict,commandHeader,delta):
        varDict['comPath']=self.comPath_TV.get()
        teensy=csSer.connectComObj(varDict['comPath'],varDict['baudRate_teensy'])
        [cVal,sChecked]=csSer.checkVariable(teensy,"{}".format(commandHeader),0.01)
        cVal=cVal+delta
        if cVal<=0:
            cVal=1
        comString=commandHeader+str(cVal)+'>'
        teensy.write(comString.encode('utf-8'))
        teensy.close()
        
    def rampTeensyChan(self,varDict,rampAmp,rampDur,\
        interRamp,rampCount,chanNum,stimType):
        varDelay = 0.01
        totalvisualStimTime=(rampDur*rampCount)+(interRamp*rampCount)
        varDict['comPath']=self.comPath_TV.get()
        teensy=csSer.connectComObj(csVar.sesVarDict['comPath'],csVar.sesVarDict['baudRate_teensy'])
        time.sleep(varDelay)
        time.sleep(varDelay)
        teensy.write("t{}{}>".format(stimType,chanNum).encode('utf-8'))
        time.sleep(varDelay)
        time.sleep(varDelay)
        teensy.write("v{}{}>".format(rampAmp,chanNum).encode('utf-8'))
        time.sleep(varDelay)
        teensy.write("d{}{}>".format(rampDur,chanNum).encode('utf-8'))
        time.sleep(varDelay)
        teensy.write("m{}{}>".format(rampCount,chanNum).encode('utf-8'))
        time.sleep(varDelay)
        teensy.write("p{}{}>".format(interRamp,chanNum).encode('utf-8'))
        time.sleep(varDelay)
        [cVal,sChecked]=csSer.checkVariable(teensy,"k",0.005)
        teensy.write("a7>".encode('utf-8'))
        time.sleep(totalvisualStimTime/1000)
        time.sleep(0.2)
        teensy.write("a0>".encode('utf-8'))
        csSer.flushBuffer(teensy)
        time.sleep(varDelay)
        teensy.close()
        
    def markOffset(self,varDict):
        # todo: add timeout
        varDict['comPath']=self.comPath_TV.get()
        teensy=csSer.connectComObj(varDict['comPath'],varDict['baudRate_teensy'])
        wVals=[]
        lIt=0
        while lIt<=20:
            [rV,vN]=csSer.checkVariable(teensy,'l',0.25)
            if vN:
                wVals.append(rV)
                lIt=lIt+1
        varDict['loadBaseline']=np.mean(wVals)-15.2
        self.offsetTV.set(float(np.mean(wVals)-15.2))
        print(float(np.mean(wVals)-15.2))
        teensy.close()
        return varDict    
    
    # d) Call outside task functions via a function.
    def do_detection(self):
        runDetectionTask()
        
    def do_trialOpto(self):
        runTrialOptoTask()
        
    def do_justRecord(self):
        runSimpleRecord()
        
class csVariables(object):
    
    def __init__(self,sesVarDict={},sensory={},timing={},optical={}):

        self.sesVarDict={'curSession':1,'comPath':'/dev/ttyACM0',\
        'baudRate_teensy':115200,'subjID':'an1','taskType':'detect','totalTrials':100,\
        'logMQTT':1,'mqttUpDel':0.05,'curWeight':20,'rigGMTZoneDif':5,'volPerRwd':0.0023,\
        'waterConsumed':0,'waterNeeded':1.5,'dirPath':'/Users/Deister/BData',\
        'hashPath':'/Users/cad','trialNum':0,'sessionOn':0,'canQuit':1,\
        'contrastChange':0,'orientationChange':1,'spatialChange':1,'dStreams':15,\
        'rewardDur':500,'lickAThr':3900,'lickLatchA':0,'minNoLickTime':1000,\
        'toTime':4000,'shapingTrial':1,'chanPlot':5,'minStim':1500,\
        'minTrialVar':200,'maxTrialVar':11000,'loadBaseline':0,'loadScale':1,\
        'serBufSize':4096,'ramp1Dur':2000,'ramp1Amp':4095,'ramp2Dur':2000,'ramp2Amp':4095,\
        'detectPlotNum':100,'updateCount':500,'plotSamps':200,'taskType':'detection',\
        'useFlybackOpto':1,'flybackScale':100,'pulsefrequency':20,'pulsedutycycle':10,\
        'firstTrialWait':10000,'pulseTrainLength':5000,\
        'startState':1,'hostName':'Compy386','experimenter':'deister','dprime':0,'criterion':0}

        # All steps go in list, even if there aren't any.
        # So: 0 steps = []; 
        # A pre-canned set: [19,22,40]
        # Special cases:
        # You can range between min/max with a code --> ":,delta" to range between min and max by delta increments 
        # example: min: 10; max: 20; steps [':',2] --> range(10,22,2) --> 10,12,14,...,18,20 

        self.timing={'trialCount':1000,'varsToUse':['trialTime','noLickTime','visualStimTime','opticalStimTime'],\
        'trialTime_min':3000,'trialTime_max':11000,'trialTime_steps':[':',1],'trialTime_probs':[0.0,0.0],\
        'noLickTime_min':599,'noLickTime_max':2999,'noLickTime_steps':[':',1],'noLickTime_probs':[0.0,0.0],\
        'visualStimTime_min':2000,'visualStimTime_max':5000,'visualStimTime_steps':[':',4],'visualStimTime_probs':[0.33,0.33],\
        'opticalStimTime_min':2000,'opticalStimTime_max':5000,'opticalStimTime_steps':[':',4],'opticalStimTime_probs':[0.33,0.33],\
        'noMotionTime_min':0,'noMotionTime_max':0,'noMotionTime_steps':[0],'noMotionTime_probs':[0.5,0.5],\
        'motionTime_min':0,'motionTime_max':0,'motionTime_steps':[0],'motionTime_probs':[0.5,0.5]}

        self.sensory={'trialCount':1000,'varsToUse':['contrast','orientation','spatialFreq','xPos','yPos','stimSize'],\
        'contrast_min':0,'contrast_max':100,'contrast_steps':[1,2,5,10,20,30,50,70],'contrast_probs':[0.2,0.2],\
        'orientation_min':0,'orientation_max':270,'orientation_steps':[90],'orientation_probs':[0.33,0.33],\
        'spatialFreq_min':4,'spatialFreq_max':5,'spatialFreq_steps':[4.5],'spatialFreq_probs':[0.70,0.15],\
        'xPos_min':0,'xPos_max':0,'xPos_steps':[-10,10],'xPos_probs':[0.6,0.0],\
        'yPos_min':0,'yPos_max':100,'yPos_steps':[-10,-10],'yPos_probs':[0.6,0.0],\
        'stimSize_min':10,'stimSize_max':14,'stimSize_steps':[13],'stimSize_probs':[0.33,0.33],\
        'piezo1_min':0,'piezo1_max':4095,'piezo1_steps':[100,200,500,1000,1500,2000,2500,3000,3500],'piezo1_probs':[0.3,0.3]}

        self.optical={'trialCount':1000,\
        'varsToUse':['c1_amp','c1_pulseDur','c1_interPulseDur','c1_pulseCount',\
        'c2_amp','c2_pulseDur','c2_interPulseDur','c2_pulseCount','c1_mask','c5_waveform'],\
        'c1_amp_min':0,'c1_amp_max':4095,'c1_amp_steps':[1000],'c1_amp_probs':[0.0,1.0],\
        'c1_pulseDur_min':10,'c1_pulseDur_max':10,'c1_pulseDur_steps':[],'c1_pulseDur_probs':[1.0,0.0],\
        'c1_interPulseDur_min':90,'c1_interPulseDur_max':90,'c1_interPulseDur_steps':[90],'c1_interPulseDur_probs':[1.0,0.0],\
        'c1_pulseCount_min':20,'c1_pulseCount_max':20,'c1_pulseCount_steps':[20],'c1_pulseCount_probs':[0.0,1.0],\
        'c2_amp_min':0,'c2_amp_max':4095,'c2_amp_steps':[1000],'c2_amp_probs':[0.0,1.0],\
        'c2_pulseDur_min':10,'c2_pulseDur_max':10,'c2_pulseDur_steps':[],'c2_pulseDur_probs':[1.0,0.0],\
        'c2_interPulseDur_min':90,'c2_interPulseDur_max':90,'c2_interPulseDur_steps':[90],'c2_interPulseDur_probs':[1.0,0.0],\
        'c2_pulseCount_min':20,'c2_pulseCount_max':20,'c2_pulseCount_steps':[20],'c2_pulseCount_probs':[0.0,1.0],\
        'c3_amp_min':0,'c3_amp_max':4095,'c3_amp_steps':[1000],'c3_amp_probs':[0.0,1.0],\
        'c3_pulseDur_min':10,'c3_pulseDur_max':10,'c3_pulseDur_steps':[],'c3_pulseDur_probs':[1.0,0.0],\
        'c3_interPulseDur_min':90,'c3_interPulseDur_max':90,'c3_interPulseDur_steps':[90],'c3_interPulseDur_probs':[1.0,0.0],\
        'c3_pulseCount_min':20,'c3_pulseCount_max':20,'c3_pulseCount_steps':[20],'c3_pulseCount_probs':[0.0,1.0],\
        'c4_amp_min':0,'c4_amp_max':4095,'c4_amp_steps':[1000],'c4_amp_probs':[0.0,1.0],\
        'c4_pulseDur_min':10,'c4_pulseDur_max':10,'c4_pulseDur_steps':[],'c4_pulseDur_probs':[1.0,0.0],\
        'c4_interPulseDur_min':90,'c4_interPulseDur_max':90,'c4_interPulseDur_steps':[90],'c4_interPulseDur_probs':[1.0,0.0],\
        'c4_pulseCount_min':20,'c4_pulseCount_max':20,'c4_pulseCount_steps':[20],'c4_pulseCount_probs':[0.0,1.0],\
        'c5_amp_min':0,'c5_amp_max':4095,'c5_amp_steps':[1000],'c5_amp_probs':[0.0,1.0],\
        'c5_pulseDur_min':10,'c5_pulseDur_max':10,'c5_pulseDur_steps':[],'c5_pulseDur_probs':[1.0,0.0],\
        'c5_interPulseDur_min':90,'c5_interPulseDur_max':90,'c5_interPulseDur_steps':[90],'c5_interPulseDur_probs':[1.0,0.0],\
        'c5_pulseCount_min':20,'c5_pulseCount_max':20,'c5_pulseCount_steps':[20],'c5_pulseCount_probs':[0.0,1.0],\
        'c1_mask_min':2,'c1_mask_max':1,'c1_mask_steps':[],'c1_mask_probs':[0.3,0.7],\
        'c2_mask_min':1,'c2_mask_max':2,'c2_mask_steps':[],'c2_mask_probs':[0.3,0.7],\
        'c5_waveform_min':0,'c5_waveform_max':1,'c5_waveform_steps':2,'c5_waveform_probs':[0.5,0.0]}
            
    def getFeatureProb(self,probDict):
        labelList = probDict['varsToUse']
        trLen = probDict['trialCount']
        
        # we make an array that is the length of 
        # the total number of trials we want numbers for.
        tempArray = np.zeros((trLen,len(labelList)))

        # we make a temporary array that is (min,max,steps) by total variables
        tempCountArray = np.zeros((3,len(labelList)))

        # we make a list of vairable names that have been iterated through. 
        # We return this list too, because it is often necessary to reconcile the item 
        varIndex = []
        
        for x in range(len(labelList)):
            curStr = labelList[x]
            varIndex.append(curStr)
            availIndicies = np.arange(trLen)
            curAvail=len(availIndicies)

            curMin=eval('probDict["{}_min"]'.format(curStr))
            curMinProb=eval('probDict["{}_probs"][0]'.format(curStr))
            curMinCount = int(np.round(curAvail*curMinProb))
            tempCountArray[0,x]=curMinCount
    
            curMax=eval('probDict["{}_max"]'.format(curStr))
            curMaxProb=eval('probDict["{}_probs"][1]'.format(curStr))
            curMaxCount = int(np.round(curAvail*curMaxProb))
            tempCountArray[1,x]=curMaxCount
            
            computeSteps = 1
            curSteps = eval('probDict["{}_steps"]'.format(curStr))

            try:
                if len(curSteps)==0:
                    computeSteps = 0
                elif curSteps[0] is ':':
                    try:
                        newSteps = []
                        rangeDelta = int(curSteps[1])
                        tempRange = range(curMin+rangeDelta,(curMax - rangeDelta)+1,rangeDelta)
                        for n in tempRange:
                            newSteps.append(n)
                        curSteps = newSteps
                    except:
                        computeSteps = 0
            except:
                # then it is singular and numeric
                computeSteps = 1
            curStepProb=1-(curMaxProb+curMinProb)
            
            if curStepProb <= 0:
                curStepCount = 0
                computeSteps = 0
            elif curStepProb > 0:
                curStepCount = int(np.round(curAvail*curStepProb))
                tempCountArray[2,x]=curStepCount
    
            # deal with mins
            np.random.shuffle(availIndicies)
            tInd=availIndicies[:curMinCount]
            tempArray[tInd,x]=curMin
            availIndicies=np.setdiff1d(availIndicies,tInd)
            curAvail=len(availIndicies)

            np.random.shuffle(availIndicies)
            tInd=availIndicies[:curMaxCount]
            tempArray[tInd,x]=curMax
            availIndicies=np.setdiff1d(availIndicies,tInd)
            curAvail=len(availIndicies)

            # C) compute steps
            if computeSteps == 1:
                try:
                    if type(curSteps) == list:
                        
                        if len(curSteps)>0:
                            for g in range(0,len(availIndicies)):
                                tempArray[availIndicies[g],x] = curSteps[np.random.randint(len(curSteps))]
                        elif len(curSteps)==0 and len(availIndicies)>0:
                            print("h2")
                            print(curStr)
                            for g in range(0,len(availIndicies)):
                                tempRand=[curMax,curMin]
                                tempArray[availIndicies[g],x] = tempRand[np.random.randint(2)]
                    else:

                        for g in range(0,len(availIndicies)):
                            tempArray[availIndicies[g],x] = curSteps
                except:
                    pass
                
        trialVar_pandaFrame = pd.DataFrame(tempArray,columns = varIndex)
        
        return trialVar_pandaFrame,tempCountArray
    
    def updateDictFromTXT(self,varDict,configF):
        for key in list(varDict.keys()):
            try:
                a = config['sesVars'][{}.format(key)]
                try:
                    a=float(a)
                    if a.is_integer():
                        a=int(a)
                    exec('varDict["{}"]={}'.format(key,a))
                except:
                    exec('varDict["{}"]="{}"'.format(key,a))
            except:
                pass
        return varDict
    
    def generateTrialVariables(self):
        [self.trialVars_sensory,_]=self.getFeatureProb(self.sensory)
        [self.trialVars_timing,_]=self.getFeatureProb(self.timing)
        [self.trialVars_optical,_]=self.getFeatureProb(self.optical)
        return self.trialVars_sensory,self.trialVars_timing,self.trialVars_optical
    
    def getRig(self):
        # returns a string that is the hostname
        mchString=socket.gethostname()
        self.hostMachine=mchString.split('.')[0]
        return self.hostMachine
    
    def dictToPandas(self,dictName):
        curKey=[]
        curVal=[]
        for key in list(dictName.keys()):
            curKey.append(key)
            curVal.append(dictName[key])
            self.pdReturn=pd.Series(curVal,index=curKey)
        return self.pdReturn
    
    def pandasToDict(self,pdName,curDict,colNum):

        varIt=0
        csvNum=0

        for k in list(pdName.index):

            if len(pdName.shape)>1:
                a=pdName[colNum][varIt]
                csvNum=pdName.shape[1]
            elif len(pdName.shape)==1:
                a=pdName[varIt]

            try:
                a=float(a)
                if a.is_integer():
                    a=int(a)
                curDict[k]=a
                varIt=varIt+1

            except:
                curDict[k]=a
                varIt=varIt+1
        
        return curDict
    
    def updateDictFromGUI(self,dictName):
        for key in list(dictName.keys()):
            try:
                a=eval('{}_TV.get()'.format(key))
                if '>' in a:
                    tSplit = a.split(',')
                    tRange = range(int(tSplit[0]),int(tSplit[2])-1)
                    exec('dictName["{}"]={}'.format(key,tRange))
                elif ',' in a and '>' not in a:
                    # then list
                    isList = 1
                elif ',' not in a and '>' not in a:
                    # then singleton           
                    try:
                        a=float(a)
                        if a.is_integer():
                            a=int(a)
                        exec('dictName["{}"]={}'.format(key,a))
                    except:
                        exec('dictName["{}"]="{}"'.format(key,a))
            except:
                pass
            
class csHDF(object):
    def __init__(self,a):
        self.a=1
    def makeHDF(self,basePath,subID,dateStamp):
        cStr=datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.sesHDF = h5py.File(basePath+"{}_behav_{}.hdf".format(subID,cStr),"a")
        return self.sesHDF
    
class csMQTT(object):
    def __init__(self):
        pass
    
    def connect_REST(self,hashPath):
        simpHash=open(hashPath)
        a=list(simpHash)
        userName = a[0].strip()
        apiKey = a[1].strip()
        self.aio = Client(userName,apiKey)
        print("mqtt: connected to aio as {}".format(self.aio.username))
        return self.aio
    
    def connect_MQTT(self,hashPath):
        simpHash=open(hashPath)
        a=list(simpHash)
        userName = a[0].strip()
        apiKey = a[1].strip()
        self.mqtt = MQTTClient(userName,apiKey)
        return self.mqtt
    
    def getMQTTLast(self,feedName,mqttObj):
        lastFeedVal='NA'
        try:
            lastFeedVal = mqttObj.receive(feedName)
        except:
            pass
        return lastFeedVal
    
    def getMQTTDataAll(self,feedName,mqttObj):
        lastFeedVal='NA'
        try:
            allFeedValues = mqttObj.data(feedName)
        except:
            pass
        return allFeedValues
    
    def makeMQTTFeed(self,feedName,mqttObj):
        try:
            feed = Feed(name=feedName.lower())
            result = mqttObj.create_feed(feed)
        except:
            pass
        
    def getMQTTFeeds(self,hashPath,mqttObj):
        feedList = []
        allFeeds = mqttObj.feeds()
        for things in allFeeds:
            feedList.append(things.name)
        return feedList
    
    def sendData(self,feedName,dataToSend,mqttObj):
        tFeed = mqttObj.feeds(feedName)
        mqttObj.send_data(tFeed.key,dataToSend)
        
    def makeSubjectFeeds(self,subjectID,mqttObj):
        subFeedLabels = ['rig','task','waterconsumed','waterneeded','weight','dprime','criterion','trials','experimenter','notes']
        subjectID = subjectID.lower()
        for x in subFeedLabels:
            feedStr = subjectID + '-' + x
            feed = Feed(name = feedStr)
            try:
                mqttObj.create_feed(feed)
            except:
                pass
            
    def getDailyConsumption(self,mqObj,sID,rigGMTDif,hourThresh,targetVol):
        
        dStamp=datetime.datetime.now().strftime("%m_%d_%Y")
        
        # we want to determine how much water the subject has had in the last day.
        # and we want to know how much water they are supposed to have.
        # we assumne they haven't had any water
        waterConsumed=0
        # and we assume they need the default volume (1.5 - 2 ml)
        waterNeeded=targetVol
        # we will eventually see how far our last data logged is from now.
        # we will assume the worst, meaning 2 hours for a session and no data logged before
        hourDif=22

        # I assume the mqtt gmt day and month is the same as our rigs day for now.
        dayOffset=0
        monthOffset=0

        # now we compute the time and normalize it relative to GMT
        rigHr=int(datetime.datetime.fromtimestamp(time.time()).strftime('%H'))
        rigHr=rigHr+rigGMTDif
        
        # now things get crazy, if you offset the rig for GMT and go over 24,
        # that means GMT has crossed the date line. 
        # thus, we need to add a day to our rig's day
        if rigHr>24:
            rigHr=rigHr-24
            dayOffset=1
        
        # Now we poll the subjects water needed feed
        try:
            tWNeed=self.getMQTTLast(sID+'-waterneeded',mqObj)
            # Look at when it was logged.
            crStr=tWNeed.created_at[0:10]
            mqHr=int(tWNeed.created_at[11:13])
            #compare year (should be a given, but never know)
            if crStr[0:4]==dStamp[6:10]:
                #compare month (less of a given)
                # I allow for a month difference of 1 in case we are on a month boundary before GMT correction.
                if abs(int(crStr[5:7])-int(dStamp[0:2]))<2:
                    # todo: add month boundary logic.
                    #compare day if there is more than a dif of 1 then can't be 12-23.9 hours dif.
                    dayDif=(int(dStamp[3:5])+dayOffset)-int(crStr[8:10])
                    if abs(dayDif)<2:
                        hourDif=rigHr-mqHr
                        if hourDif<=hourThresh:
                            # after all that, if the time since the last data point is less than our time threshold
                            # which is usually 12 hours, we use the feed's value as truth.
                            waterNeeded=float('{:0.4f}'.format(float(tWNeed.value)))
        except:
            pass

        # now we need to do the same for what has been consumed
        try:
            gDP=self.getMQTTLast(sID+'-waterconsumed',mqObj)
            # Look at when it was logged.
            crStr=gDP.created_at[0:10]
            mqHr=int(gDP.created_at[11:13])
            #compare year (should be a given, but never know)
            if crStr[0:4]==dStamp[6:10]:
                #compare month (less of a given)
                # I allow for a month difference of 1 in case we are on a month boundary before GMT correction.
                if abs(int(crStr[5:7])-int(dStamp[0:2]))<2:
                    # todo: add month boundary logic.
                    #compare day if there is more than a dif of 1 then can't be 12-23.9 hours dif.
                    dayDif=(int(dStamp[3:5])+dayOffset)-int(crStr[8:10])
                    if abs(dayDif)<2:
                        hourDif=rigHr-mqHr
                        if hourDif<=hourThresh:
                            waterConsumed=float('{:0.4f}'.format(float(gDP.value)))
        except:
            waterConsumed=0
            hourDif = 0
        
        self.waterNeeded=waterNeeded
        self.waterConsumed=waterConsumed
        self.hourDif=hourDif
        self.dStamp=dStamp
        
        return self.waterConsumed,self.waterNeeded,self.hourDif,self.dStamp
    
    def openGoogleSheet(self,gAPIHashPath):
        #gAPIHashPath='/Users/cad/simpHashes/client_secret.json'
        self.gc = pygsheets.authorize(gAPIHashPath)
        return self.gc
    
    def updateGoogleSheet(self,sheetCon,subID,cellID,valUp):
        sh = sheetCon.open('WR Log')
        wsTup=sh.worksheets()
        wks = sh.worksheet_by_title(subID)
        curData=np.asarray(wks.get_all_values(returnas='matrix'))
        dd=np.where(curData==cellID)
        # Assuming indexes are in row 1, then I just care about dd[1]
        varCol=dd[1]+1
        # now let's figure out which row to update
        entries=curData[:,dd[1]]
        # how many entries exist in that column
        numRows=len(entries)
        lastEntry=curData[numRows-1,dd[1]]
        if lastEntry=='':
            wks.update_cell((numRows,varCol),valUp)
            self.updatedRow=numRows
            self.updatedCol=varCol
        elif lastEntry != '':
            wks.update_cell((numRows+1,varCol),valUp)
            self.updatedRow=numRows
            self.updatedCol=varCol
        return 
    
class csSerial(object):
    
    def __init__(self,a):
        self.a=1
    
    def connectComObj(self,comPath,baudRate):
        # self.comObj = serial.Serial(comPath,baudRate,timeout=0)
        self.comObj = serial.Serial(comPath,baudRate)
        self.comObj.close()
        self.comObj.open()
        return self.comObj
    
    def readSerialBuffer(self,comObj,curBuf,bufMaxSize):
        
        comObj.timeOut=0
        curBuf=curBuf+comObj.read(1)
        curBuf=curBuf+comObj.read(min(bufMaxSize-1, comObj.in_waiting))
        i = curBuf.find(b"\n")
        r = curBuf[:i+1]
        curBuf = curBuf[i+1:]
        
        echoDecode=bytes()
        tDataDecode=bytes()
        eR=[]
        sR=[]

        eB=r.find(b"echo")
        eE=r.find(b"~")
        tDB=r.find(b"tData")
        tDE=r.find(b"\r")

        if eB>=0 and eE>=1:
            echoDecode=r[eB:eE+1]
            eR=echoDecode.strip().decode()
            eR=eR.split(',')
        if tDB>=0 and tDE>=1:
            tDataDecode=r[tDB:tDE]
            sR=tDataDecode.strip().decode()
            sR=sR.split(',')

        self.curBuf = curBuf
        self.echoLine = eR
        self.dataLine = sR
        return self.curBuf,self.echoLine,self.dataLine
    
    def readSerialData(self,comObj,headerString,varCount):
        sR=[]
        newData=0
        bytesAvail=comObj.inWaiting()

        if bytesAvail>0:
            sR=comObj.readline().strip().decode()
            sR=sR.split(',')
            if len(sR)==varCount and sR[0]==headerString:
                newData=1

        self.sR=sR
        self.newData=newData
        self.bytesAvail = bytesAvail
        return self.sR,self.newData,self.bytesAvail
    
    def flushBuffer(self,comObj):
        while comObj.inWaiting()>0:
            sR=comObj.readline().strip().decode()
            sR=[]
            
    def checkVariable(self,comObj,headChar,fltDelay):
        comObj.write('{}<'.format(headChar).encode('utf-8'))
        time.sleep(fltDelay)
        [tString,self.dNew,self.bAvail]=self.readSerialData(comObj,'echo',4)
        if self.dNew:
            if tString[1]==headChar:
                self.returnVar=int(tString[2])
        elif self.dNew==0:
            self.returnVar=0
        return self.returnVar,self.dNew

    def sendAnalogOutValues(self,comObj,varChar,sendValues):
        # Specific to csStateBehavior defaults.
        # Analog output is handled by passing a variable and specifying a channel (1-X)
        for x in sendValues:
            comObj.write('{}{}{}>'.format(varChar,sendValues[0],x+1).encode('utf-8'))

    def sendVisualValues(self,comObj,trialNum):
        comObj.write('c{}>'.format(int(csVar.contrast[trialNum])).encode('utf-8'))
        comObj.write('o{}>'.format(int(csVar.orientation[trialNum])).encode('utf-8'))
        comObj.write('s{}>'.format(int(csVar.spatialFreq[trialNum])).encode('utf-8'))

    def sendVisualPlaceValues(self,comObj,trialNum):
        comObj.write('z{}>'.format(int(csVar.stimSize[trialNum])).encode('utf-8'))
        comObj.write('x{}>'.format(int(csVar.xPos[trialNum])).encode('utf-8'))
        comObj.write('y{}>'.format(int(csVar.yPos[trialNum])).encode('utf-8'))
        
class csPlot(object):
    def __init__(self,pClrs={}):
        self.pClrs={'right':'#D9220D','cBlue':'#33A4F3','cPurp':'#6515D9',\
        'cOrange':'#F7961D','left':'cornflowerblue','cGreen':'#29AA03'}
    def initializeDetectFigVars(self,stPlotX={},stPlotY={},stPlotRel={},pClrs={},pltX=[],pltY=[]):
        self.stPlotX={'init':0.10,'wait':0.10,'stim':0.30,'catch':0.30,'rwd':0.50,'TO':0.50}
        self.stPlotY={'init':0.65,'wait':0.40,'stim':0.52,'catch':0.28,'rwd':0.52,'TO':0.28}
        # # todo:link actual state dict to plot state dict, now its a hack
        self.stPlotRel={'0':0,'1':1,'2':2,'3':3,'4':4,'5':5}
        self.pltX=[]
        for xVals in list(self.stPlotX.values()):
            self.pltX.append(xVals)
        self.pltY=[]
        for yVals in list(self.stPlotY.values()):
            self.pltY.append(yVals)
            
    def initializeOptoFigVars(self,stPlotX={},stPlotY={},stPlotRel={},pClrs={},pltX=[],pltY=[]):
        self.stPlotX={'init':0.10,'wait':0.10,'stim':0.30}
        self.stPlotY={'init':0.65,'wait':0.40,'stim':0.52}
        # # todo:link actual state dict to plot state dict, now its a hack
        self.stPlotRel={'0':0,'1':1,'2':7,'2':8}
        self.pltX=[]
        for xVals in list(self.stPlotX.values()):
            self.pltX.append(xVals)
        self.pltY=[]
        for yVals in list(self.stPlotY.values()):
            self.pltY.append(yVals)
            
    def makeTrialFig_detection(self,fNum):
        try:
            plt.close(fNum)
        except:
            pass
        dGrid = plt.GridSpec(9, 2, wspace=0.2, hspace=0.2) # 1 row, 5 col , wspace=0.4, hspace=0.3
        self.initializeDetectFigVars()
        self.binDP=[]
        # Make feedback figure.
        #figure(num=None, figsize=(8, 6), dpi=80, facecolor='w', edgecolor='k')
        self.trialFig = plt.figure(fNum,figsize=(5,3))
        self.trialFramePosition='+250+0' # can be specified elsewhere
        mng = plt.get_current_fig_manager()
        eval('mng.window.wm_geometry("{}")'.format(self.trialFramePosition))
        plt.show(block=False)
        self.trialFig.canvas.flush_events()

        self.stAxes=self.trialFig.add_subplot(dGrid[0, 0:]) 
        self.stAxes.set_axis_off()
        self.stText = self.stAxes.text(0.5,0.1,'trial # {} of {}; State # {}'.format([],[],0),\
            bbox={'facecolor':'w', 'alpha':0.0, 'pad':5},transform=self.stAxes.transAxes, ha="center")
        plt.show(block=False)
        self.trialFig.canvas.flush_events()
        self.stAxes.draw_artist(self.stText)
        self.stAxes.draw_artist(self.stAxes.patch)
        self.trialFig.canvas.flush_events()

        # add the lickA axes and lines.
        self.lA_Axes=self.trialFig.add_subplot(dGrid[1:4,0:]) #col,rows
        self.lA_Axes.set_ylim([-100,1200])
        self.lA_Axes.set_xticks([])
        # self.lA_Axes.set_yticks([])
        self.lA_Line,=self.lA_Axes.plot([],color="cornflowerblue",lw=1)
        self.trialFig.canvas.draw_idle()
        plt.show(block=False)
        self.trialFig.canvas.flush_events()
        self.lA_Axes.draw_artist(self.lA_Line)
        self.lA_Axes.draw_artist(self.lA_Axes.patch)
        self.trialFig.canvas.flush_events()

        # OUTCOME AXES
        self.outcomeAxis=self.trialFig.add_subplot(dGrid[5:8,0]) #col,rows
        self.outcomeAxis.axis([-2,100,-0.2,5.2])
        self.outcomeAxis.yaxis.tick_left()
        self.stimOutcomeLine,=self.outcomeAxis.plot([],[],marker="o",markeredgecolor="black",\
            markerfacecolor="cornflowerblue",markersize=12,lw=0,alpha=0.5,markeredgewidth=2)
        self.noStimOutcomeLine,=self.outcomeAxis.plot([],[],marker="o",markeredgecolor="black",\
            markerfacecolor="red",markersize=12,lw=0,alpha=0.5,markeredgewidth=2)
        self.outcomeAxis.set_title('dprime: ',fontsize=10)
        self.binDPOutcomeLine,=self.outcomeAxis.plot([],[],color="black",lw=1)
        plt.show(block=False)
        self.trialFig.canvas.flush_events()
        self.outcomeAxis.draw_artist(self.stimOutcomeLine)
        self.outcomeAxis.draw_artist(self.noStimOutcomeLine)
        self.outcomeAxis.draw_artist(self.binDPOutcomeLine)
        self.outcomeAxis.draw_artist(self.outcomeAxis.patch)
        
    def quickUpdateTrialFig(self,trialNum,totalTrials,curState):
        self.trialFig.canvas.flush_events()
        
    def updateTrialFig(self,xData,yData,trialNum,totalTrials,curState,yLims):
        try:
            self.stText.set_text('trial # {} of {}; State # {}'.format(trialNum,totalTrials,curState))
            self.lA_Line.set_xdata(xData)
            self.lA_Line.set_ydata(yData)
            self.lA_Axes.set_xlim([xData[0],xData[-1]])
            self.lA_Axes.set_ylim([yLims[0],yLims[1]])
            self.lA_Axes.draw_artist(self.lA_Line)
            self.lA_Axes.draw_artist(self.lA_Axes.patch)
            self.stAxes.draw_artist(self.stText)
            self.stAxes.draw_artist(self.stAxes.patch)
            self.trialFig.canvas.draw_idle()
            self.trialFig.canvas.flush_events()
        except:
             pass
         
    def updateStateFig(self,curState):
        try:
            self.stAxes.draw_artist(self.stText)
            self.stAxes.draw_artist(self.stAxes.patch)
            self.trialFig.canvas.draw_idle()
            self.trialFig.canvas.flush_events()
        except:
             pass
         
    def updateOutcome(self,stimTrials,stimResponses,noStimTrials,noStimResponses,totalTrials):
        sM=0.001
        nsM=0.001
        dpBinSz=10

        if len(stimResponses)>0:
            sM=np.mean(stimResponses)
        if len(noStimResponses)>0:
            nsM=np.mean(noStimResponses)

        dpEst=norm.ppf(max(sM,0.0001))-norm.ppf(max(nsM,0.0001))
        
        self.outcomeAxis.set_title('dprime: {:0.3f}'.format(dpEst),fontsize=10)
        self.stimOutcomeLine.set_xdata(stimTrials)
        self.stimOutcomeLine.set_ydata(stimResponses)
        self.noStimOutcomeLine.set_xdata(noStimTrials)
        self.noStimOutcomeLine.set_ydata(noStimResponses)
        
        if len(noStimResponses)>0 and len(stimResponses)>0:
            sMb=int(np.mean(stimResponses[-dpBinSz:])*100)*0.01
            nsMb=int(np.mean(noStimResponses[-dpBinSz:])*100)*0.01
            self.binDP.append(norm.ppf(max(sMb,0.0001))-norm.ppf(max(nsMb,0.0001)))
            self.binDPOutcomeLine.set_xdata(np.linspace(1,len(self.binDP),len(self.binDP)))
            self.binDPOutcomeLine.set_ydata(self.binDP)
            self.outcomeAxis.draw_artist(self.binDPOutcomeLine)
        
        self.outcomeAxis.set_xlim([-1,totalTrials+1])
        self.outcomeAxis.draw_artist(self.stimOutcomeLine)
        self.outcomeAxis.draw_artist(self.noStimOutcomeLine)
        self.outcomeAxis.draw_artist(self.outcomeAxis.patch)

        self.trialFig.canvas.draw_idle()
        self.trialFig.canvas.flush_events()

# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
# $$$$$$$$$$    Main Program Body    $$$$$$$$$$$$$
# $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# >>> Make Class Instances <<< #
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #

csVar=csVariables(1)

try:
    config = configparser.ConfigParser()
    config.read(sys.argv[1])
    csGui.useGUI = int(config['settings']['useGUI'])

    #todo: show sinda this pattern
    #todo: loop through what could be in the config obj, or is
    try:
        csVar.sesVarDict['taskType'] = config['sesVars']['taskType']
        csVar.sesVarDict['comPath'] = config['sesVars']['comPath']
        csVar.sesVarDict['dirPath'] = config['sesVars']['savePath']
        csVar.sesVarDict['hashPath'] = config['sesVars']['hashPath']
        csVar.sesVarDict['subjID'] = config['sesVars']['subjID']
    except:
        print("issue with config vars")
except:
    useGUI=1
    print("using gui ...")
    root = Tk()
    csGui = csGUI(csVar.sesVarDict,csVar.timing,csVar.sensory,csVar.optical)
    csGui.makeParentWindow(root,csVar.sesVarDict,csVar.timing,csVar.sensory,csVar.optical)

if csGui.useGUI == 0:
    print("not using gui")
    csGui = csGUI(csVar.sesVarDict,csVar.timing,csVar.sensory,csVar.optical)
    csGui.loadPandaSeries(csVar.sesVarDict['dirPath'] ,csVar.sesVarDict,csVar.timing,csVar.sensory,csVar.optical)

csSesHDF=csHDF(1)
csAIO=csMQTT()
csSer=csSerial(1)
csPlt=csPlot(1)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# >>> Common Tasks Functions <<<
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def makeTrialVariables():
    for x in csVar.sensory['varsToUse']:
        exec("csVar.{}=[]".format(x))
    for x in csVar.timing['varsToUse']:
        exec("csVar.{}=[]".format(x))
    for x in csVar.optical['varsToUse']:
        exec("csVar.{}=[]".format(x))
    # Second, generate the first set of variables
    csVar.generateTrialVariables()
    csVar.trialVars_timing.to_csv(csVar.sesVarDict['dirPath'] + '/' +'testTiming.csv')
    csVar.trialVars_optical.to_csv(csVar.sesVarDict['dirPath'] + '/' +'testOptical.csv')
    csVar.trialVars_sensory.to_csv(csVar.sesVarDict['dirPath'] + '/' +'testSensory.csv')
    
def initializeTeensy():
    teensy=csSer.connectComObj(csVar.sesVarDict['comPath']\
        ,csVar.sesVarDict['baudRate_teensy'])
    # D) Flush the teensy serial buffer. Send it to the init state (#0).
    csSer.flushBuffer(teensy)
    teensy.write('a0>'.encode('utf-8'))
    time.sleep(0.01)

    sChecked=0
    while sChecked==0:
        [tTeensyState,sChecked]=csSer.checkVariable(teensy,'a',0.005)

    print(sChecked)
    while tTeensyState != 0:
        print("not in 0, will force")
        teensy.write('a0>'.encode('utf-8'))
        time.sleep(0.005)
        cReturn=csSer.checkVariable(teensy,'a',0.005)
        if cReturn(1)==1:
            tTeensyState=cReturn(0)

    return teensy,tTeensyState

def initializeLoadCell():
    try:
        wVals=[]
        lIt=0
        while lIt<=10:
            [rV,vN]=csSer.checkVariable(teensy,'l',0.2)
            if vN:
                wVals.append(rV)
                lIt=lIt+1
        csVar.sesVarDict['curWeight']=(np.mean(wVals)-csVar.sesVarDict['loadBaseline'])*0.1;
        preWeight=csVar.sesVarDict['curWeight']
        print("pre weight={}".format(preWeight))
        tNote = 'pre-session weight = {}'.format(preWeight)
        csGui.curNotes.append(tNote)
        if csVar.sesVarDict['logMQTT']==1:
            csGui.makeNotes(csVar.sesVarDict['subjID'] + '-notes',tNote,csVar.sesVarDict)
    except:
        csVar.sesVarDict['curWeight']=0
        csGui.curNotes.append('pre-session weight = {}'.format(0))
        
def mqttStart():
    # subFeedLabels = ['rig','task','waterconsumed','waterneeded','weight','performance','notes']
    tdStamp=datetime.datetime.now().strftime("%Y_%m_%d_%H:%M:%S")
    csGui.curNotes.append('session start: ' + '{}'.format(tdStamp))
    csVar.sesVarDict['logMQTT'] = csGui.logMQTT_TV.get()
    tMqLog = csVar.sesVarDict['logMQTT']
    csGui.curNotes.append(tMqLog)
    hPath = csVar.sesVarDict['hashPath'] + '/simpHashes/csIO.txt'
    tDelay = csVar.sesVarDict['mqttUpDel']

    tWeight = csVar.sesVarDict['curWeight']
    csVar.sesVarDict['hostName'] = csVar.getRig().lower()
    tSubj = csVar.sesVarDict['subjID'].lower()
    
    csGui.curNotes.append("subject: {}".format(tSubj))
    csGui.curNotes.append("mqtt logging: {}".format(tMqLog))
    csGui.curNotes.append("host name: {}".format(csVar.sesVarDict['hostName']))
    csGui.curNotes.append("task type: {}".format(csVar.sesVarDict['taskType']))
    csGui.curNotes.append("session number: {}".format(csVar.sesVarDict['curSession']))
    csGui.curNotes.append("experimenter: {}".format(csVar.sesVarDict['experimenter']))

    if tMqLog==1:
        aio=csAIO.connect_REST(hPath)
        csAIO.makeSubjectFeeds(tSubj,aio)
        csAIO.makeMQTTFeed('rig-' + csVar.sesVarDict['hostName'],aio)
        csVar.sesVarDict['waterConsumed'],csVar.sesVarDict['waterNeeded'],_,_ = \
        csAIO.getDailyConsumption(aio,tSubj,csVar.sesVarDict['rigGMTZoneDif'],12,csVar.sesVarDict['waterNeeded'])

        # make a prediction about consumption
        topAmount=csVar.sesVarDict['waterNeeded']-csVar.sesVarDict['waterConsumed']
        predTrials = int(topAmount/csVar.sesVarDict['volPerRwd'])
        if predTrials < 0:
            predTrials = 0
        print('mqtt: {} still needs {:0.4f} mL of water today'.format(tSubj,topAmount))
        print('mqtt: {} should run at least {} rewarded trials'.format(tSubj,predTrials))
        
        if len(aio.username) == 0:
            print("mqtt: did not connect to mqtt broker: you are probably offline")
            csVar.sesVarDict['logMQTT'] = 0
        
        elif len(aio.username) > 0:
            print('logged into aio (mqtt broker)')
            
            try:
                csAIO.sendData(tSubj + '-weight',tWeight,aio)
                time.sleep(tDelay)
                csAIO.sendData(tSubj + '-task',csVar.sesVarDict['taskType'],aio)
                time.sleep(tDelay)
                csAIO.sendData(tSubj + '-experimenter',csVar.sesVarDict['experimenter'],aio)
                time.sleep(tDelay)
                csAIO.sendData(tSubj + '-rig',csVar.sesVarDict['hostName'] + '-on',aio)
                time.sleep(tDelay)
                csAIO.sendData('rig-' + csVar.sesVarDict['hostName'],1,aio)
                time.sleep(tDelay)
                
            except:
                print('mqtt: logging issue')
        try:
            print('logging to sheet')
            gHashPath=csVar.sesVarDict['hashPath'] + '/simpHashes/client_secret.json'
            gSheet=csAIO.openGoogleSheet(gHashPath)
            csAIO.updateGoogleSheet(gSheet,csVar.sesVarDict['subjID'],'Weight Pre',csVar.sesVarDict['curWeight'])
            print('logged to sheet')
        except:
            print('did not log to google sheet')
    elif csVar.sesVarDict['logMQTT']!=1:
        aio =[]
    return aio

def mqttStop(mqttObj):
    
    tDelay = csVar.sesVarDict['mqttUpDel']
    if csVar.sesVarDict['logMQTT']==1:
        waterConsumed = csVar.sesVarDict['waterConsumed']
        waterNeeded = float(csVar.sesVarDict['waterNeeded'])
        tDPrime = csVar.sesVarDict['dprime']
        tCriterion = csVar.sesVarDict['criterion']
        loadCellChan = 4
        tSubj = csVar.sesVarDict['subjID'].lower()
        try:
            waterNeeded=float(waterNeeded)-float(waterConsumed)
            csVar.sesVarDict['curWeight']=0
            # todo: fix the post weight
            # (np.mean(sesData[csVar.loopCnt-plotSamps:csVar.loopCnt,4])-csVar.sesVarDict['loadBaseline'])*0.1
            
            if waterNeeded<0:
                waterNeeded=0
                csVar.sesVarDict['waterNeeded'] = 0
            try:
                csAIO.sendData(tSubj + '-weight',csVar.sesVarDict['curWeight'],mqttObj)
                time.sleep(tDelay)
                csAIO.sendData('rig-' + csVar.sesVarDict['hostName'],0,mqttObj)
                time.sleep(tDelay)
                csAIO.sendData(tSubj + '-rig',csVar.sesVarDict['hostName'] + '-off',mqttObj)
                time.sleep(tDelay)
                csAIO.sendData(tSubj + '-waterconsumed',waterConsumed,mqttObj)
                time.sleep(tDelay)
                csAIO.sendData(tSubj + '-waterneeded',waterNeeded,mqttObj)
                time.sleep(tDelay)
                csAIO.sendData(tSubj + '-dprime',tDPrime,mqttObj)
                time.sleep(tDelay)
                csAIO.sendData(tSubj + '-criterion',tCriterion,mqttObj)
                time.sleep(tDelay)
                csAIO.sendData(tSubj + '-trials',csVar.sesVarDict['trialNum'],mqttObj)
                time.sleep(tDelay)
            except:
                print('mqtt: logging issue')
            
            # Google Sheet Stuff
            try:
                gDStamp=datetime.datetime.now().strftime("%m/%d/%Y")
                gTStamp=datetime.datetime.now().strftime("%H:%M:%S")
            except:
                print('did not log to google sheet')
        
            try:
                print('attempting to log to sheet')
                gSheet=csAIO.openGoogleSheet(gHashPath)
                canLog=1
            except:
                print('failed to open google sheet')
                canLog=0
        
            if canLog==1:
                try:
                    csAIO.updateGoogleSheet(gSheet,csVar.sesVarDict['subjID'],\
                        'Weight Post',csVar.sesVarDict['curWeight'])
                    csAIO.updateGoogleSheet(gSheet,csVar.sesVarDict['subjID'],\
                        'Delivered',csVar.sesVarDict['waterConsumed'])
                    csAIO.updateGoogleSheet(gSheet,csVar.sesVarDict['subjID'],\
                        'Place',csVar.sesVarDict['hostName'])
                    csAIO.updateGoogleSheet(gSheet,csVar.sesVarDict['subjID'],\
                        'Date Stamp',gDStamp)
                    csAIO.updateGoogleSheet(gSheet,csVar.sesVarDict['subjID'],\
                        'Time Stamp',gTStamp)
                except:
                    print('did not log some things to sheet')
        except:
            pass
        
def writeData(hdfObj,sessionNumber,sessionData,attributeLabels,attributeData):
    
    hdfObj["session_{}".format(sessionNumber)]=sessionData
    for x in csVar.sensory['varsToUse']:
        hdfObj["session_{}".format(sessionNumber)].attrs[x]=eval('csVar.' + x)
    for x in csVar.timing['varsToUse']:
        hdfObj["session_{}".format(sessionNumber)].attrs[x]=eval('csVar.' + x)
    for x in csVar.optical['varsToUse']:
        hdfObj["session_{}".format(sessionNumber)].attrs[x]=eval('csVar.' + x)
    
    atCount = 0
    for idx in csVar.attributeLabels:
        hdfObj["session_{}".format(sessionNumber)].attrs[attributeLabels[atCount]]=attributeData[atCount]
        atCount = atCount+1
    # also add notes
    try:
        hdfObj["session_{}".format(sessionNumber)].attrs['notes']=[v.encode('utf8') for v in csGui.curNotes]
    except:
        pass
    hdfObj.close()
    
def getThisTrialsVariables(trialNumber):
    for x in csVar.timing['varsToUse']:
        tVal = csVar.trialVars_timing[x][trialNumber]
        eval("csVar.{}.append({})".format(x,tVal))

    for x in csVar.sensory['varsToUse']:
        tVal = csVar.trialVars_sensory[x][trialNumber]
        eval("csVar.{}.append({})".format(x,tVal))

    for x in csVar.optical['varsToUse']:
        tVal = csVar.trialVars_optical[x][trialNumber]
        eval("csVar.{}.append({})".format(x,tVal))
        
def updateTaskVars():
    # a) Check variables related to whether we keep running, or not. 
    if csGui.useGUI==1:
        # if we are using the GUI, we need to check to see if the user has changed text variables. 
        csVar.sesVarDict['totalTrials']=int(csGui.totalTrials_TV.get())
        try:
            csVar.sesVarDict['shapingTrial']=int(csGui.shapingTrial_TV.get())
        except:
            csVar.sesVarDict['shapingTrial']=0
            shapingTrial_TV.set('0')
        csVar.sesVarDict['useFlybackOpto']=int(csGui.useFlybackOpto_TV.get())
        csVar.sesVarDict['lickAThr']=int(csGui.lickAThr_TV.get())
        csVar.sesVarDict['chanPlot']=csGui.chanPlotIV.get()
        if csVar.sesVarDict['trialNum']>csVar.sesVarDict['totalTrials']:
            csVar.sesVarDict['sessionOn']=0
            
def initializeTasks():
    csVar.attributeLabels = ['stimTrials','noStimTrials','responses','binaryStim','trialDurs']
    csVar.attributeData=[[],[],[],[],[]]
    csVar.curTime = 0
    csVar.curStateTime = 0
    csVar.curInt = 0

    if csGui.useGUI==1:
        csPlt.makeTrialFig_detection(csVar.sesVarDict['detectPlotNum'])
        csVar.sesVarDict=csGui.updateDictFromGUI(csVar.sesVarDict)
    elif csGui.useGUI==0:
        config.read(sys.argv[1])
        csVar.sesVarDict=csVar.updateDictFromTXT(csVar.sesVarDict,config)
    makeTrialVariables()
    # connect to the teensy
    [csSer.teensy,csSer.tState] = initializeTeensy()   
    initializeLoadCell()
    csAIO.mAIO = mqttStart()
    csVar.sesVarDict['sessionOn']=1
    csVar.sesVarDict['canQuit']=0
    if csGui.useGUI==1:
        csGui.quitButton['text']="End Ses"

    csVar.sesVarDict['sampRate']=1000
    csVar.sesVarDict['maxDur']=3600*2*csVar.sesVarDict['sampRate']
    csVar.sesData = np.memmap(csVar.sesVarDict['dirPath'] + '/' + 'sesDataMemMap.npy',\
        mode='w+',dtype=np.int32,shape=(csVar.sesVarDict['maxDur'],csVar.sesVarDict['dStreams']))
    csVar.sesHDF=csSesHDF.makeHDF(csVar.sesVarDict['dirPath'] +'/',csVar.sesVarDict['subjID'] + '_ses{}'.\
        format(csVar.sesVarDict['curSession']),datetime.datetime.now().strftime("%m_%d_%Y"))
    csVar.pyState=csVar.sesVarDict['startState']
    csSer.serialBuf=bytearray()
    csVar.trialSamps=[0,0]
    csVar.sampLog=[]
    csVar.sList=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
    csVar.sHeaders=np.zeros(len(csVar.sList))
    if csGui.useGUI==1:
        csGui.toggleTaskButtons(0)
    csVar.sesVarDict['trialNum']=0
    csVar.sesVarDict['lickLatchA']=0
    
    csVar.outSyncCount=0
    csVar.serialVarTracker = [0,0,0,0,0,0,0,0]
    csVar.stateSync=0
    csVar.loopCnt=0

    csVar.lastLick=0
    csVar.lickCounter=0
    csVar.lastLickCount=0
    csSer.teensy.write('a1>'.encode('utf-8')) 
    # generic "report" variable
    csVar.reported = 0
    
def checkTeensyData():
    newData=0
    [csSer.serialBuf,eR,tString]=csSer.readSerialBuffer(csSer.teensy,csSer.serialBuf,csVar.sesVarDict['serBufSize'])
    if len(tString)==csVar.sesVarDict['dStreams']-1:
        newData =1
        # handle timing stuff
        intNum = int(tString[1])
        tTime = int(tString[2])
        tStateTime=int(tString[3])
        # if time did not go backward (out of order packet) 
        # then increment python time, int, and state time.
        if (tTime >= csVar.curTime):
            csVar.curTime  = tTime
            csVar.cutInt = intNum
            csVar.curStateTime = tStateTime
        
        # check the teensy state
        csSer.tState=int(tString[4])
        
        # even if the the data came out of order, we need to assign it to the right part of the array.
        for x in range(0,csVar.sesVarDict['dStreams']-2):
            csVar.sesData[intNum,x]=int(tString[x+1])
        csVar.sesData[intNum,csVar.sesVarDict['dStreams']-2]=csVar.pyState # The state python wants to be.
        csVar.sesData[intNum,csVar.sesVarDict['dStreams']-1]=0 # Thresholded licks
        csVar.loopCnt=csVar.loopCnt+1
    
    return newData

def updatePlots():
    # d) If we are using the GUI plot updates ever so often.
    if csGui.useGUI==1:
        plotSamps=csVar.sesVarDict['plotSamps']
        updateCount=csVar.sesVarDict['updateCount']
        lyMin=-1
        lyMax=4098
        if csVar.sesVarDict['chanPlot']==11 or csVar.sesVarDict['chanPlot']==7:
            lyMin=-0.1
            lyMax=1.1
        if csVar.loopCnt>plotSamps and np.mod(csVar.loopCnt,updateCount)==0:
            if csVar.sesVarDict['chanPlot']==0:
                csPlt.quickUpdateTrialFig(csVar.sesVarDict['trialNum'],\
                    csVar.sesVarDict['totalTrials'],csSer.tState)
            elif csVar.sesVarDict['chanPlot'] != 0:
                csPlt.updateTrialFig(np.arange(len(csVar.sesData[csVar.loopCnt-plotSamps:csVar.loopCnt,\
                    csVar.sesVarDict['chanPlot']])),csVar.sesData[csVar.loopCnt-plotSamps:csVar.loopCnt,\
                csVar.sesVarDict['chanPlot']],csVar.sesVarDict['trialNum'],\
                    csVar.sesVarDict['totalTrials'],csSer.tState,[lyMin,lyMax])
                                                                  
def lickDetection(sensorChan = 5,latchTime=50):
    # e) Lick detection. This can be done in hardware, but I like software because thresholds can be dynamic.
    if csVar.sesData[csVar.cutInt,sensorChan]>=csVar.sesVarDict['lickAThr'] and csVar.sesVarDict['lickLatchA']==0:
        csVar.sesData[csVar.cutInt,csVar.sesVarDict['dStreams']-1]=1
        csVar.sesVarDict['lickLatchA']=latchTime
        # these are used in states
        csVar.lickCounter=csVar.lickCounter+1
        csVar.lastLick=csVar.curStateTime

    elif csVar.sesVarDict['lickLatchA']>0:
        csVar.sesVarDict['lickLatchA']=csVar.sesVarDict['lickLatchA']-1
        
def stateResolution():
    # f) Resolve state.
    # if the python side's desired state differs from the actual Teensy state
    # then note in python we are out of sync, and try again next loop.
    if csVar.pyState == csSer.tState:
        csVar.stateSync=1
    elif csVar.pyState != csSer.tState:
        csVar.stateSync=0

    # If we are out of sync for too long, then push another change over the serial line.
    # ******* This is a failsafe, but it shouldn't really happen.
    if csVar.stateSync==0:
        csVar.outSyncCount=csVar.outSyncCount+1
        if csVar.outSyncCount>=200:
            csSer.teensy.write('a{}>'.format(csVar.pyState).encode('utf-8'))  
            
def genericHeader():
    csVar.trialSamps[0]=csVar.loopCnt-1
    # reset counters that track state stuff.
    csVar.lickCounter=0
    csVar.lastLickCount = 0
    csVar.lastLick=0  
    csVar.reported =0                  
    csVar.outSyncCount=0
    csVar.serialVarTracker = [0,0,0,0,0,0,0,0]
    csVar.sHeaders[csVar.pyState]=1
    csVar.sHeaders[np.setdiff1d(csVar.sList,csVar.pyState)]=0
    
def trialMaintenance():
    # g) Trial resolution.
    tTrial = csVar.sesVarDict['trialNum']
    getThisTrialsVariables(tTrial)
    csVar.sesVarDict['minStim']=csVar.visualStimTime[tTrial]
    csVar.waitTime = csVar.trialTime[tTrial]
    csVar.lickWaitTime = csVar.noLickTime[tTrial]

    csVar.serialVarTracker = [0,0,0,0,0,0,0,0]
    csVar.tTrial = tTrial

    # 2) if we aren't using the GUI, we can still change variables, like the number of trials etc.
    # in the text file. However, we shouldn't poll all the time because we have to reopen the file each time. 
    # We do so here. 
    if csGui.useGUI==0:
        config.read(sys.argv[1])
        csVar.sesVarDict['totalTrials'] = int(config['sesVars']['totalTrials'])
        csVar.sesVarDict['lickAThr'] = int(config['sesVars']['lickAThr'])
        csVar.sesVarDict['volPerRwd'] = float(config['sesVars']['volPerRwd'])

        if csVar.sesVarDict['trialNum']>csVar.sesVarDict['totalTrials']:
            csVar.sesVarDict['sessionOn']=0
    
    # 3) incrment the trial count and 
    csVar.sesVarDict['trialNum']=csVar.sesVarDict['trialNum']+1

    # 4) inform the user via the terminal what's going on.
    print('starting trial #{} of {}'.format(csVar.sesVarDict['trialNum'],csVar.sesVarDict['totalTrials']))
    print('target contrast: {:0.2f} ; orientation: {}'.format(csVar.contrast[csVar.tTrial],csVar.orientation[csVar.tTrial]))
    print('target xpos: {} ; size: {}'.format(csVar.xPos[csVar.tTrial],csVar.stimSize[csVar.tTrial]))
    print('estimated trial time = {:0.3f} seconds'.format((csVar.noLickTime[csVar.tTrial] + csVar.trialTime[csVar.tTrial])*0.001))
    
def setupVisualStim(featureSendTime,placementSendTime):
    # update visual stim params on the Teensy
    # first 
    if csVar.serialVarTracker[0] == 0 and csVar.curStateTime>=featureSendTime:
        csSer.sendVisualValues(csSer.teensy,csVar.tTrial)
        csVar.serialVarTracker[0]=1

    elif csVar.serialVarTracker[1] == 0 and csVar.curStateTime>=placementSendTime:
        csSer.sendVisualPlaceValues(csSer.teensy,csVar.tTrial)
        csVar.serialVarTracker[1] = 1
        
def enforceNoLickRule():
    if csVar.lickCounter>csVar.lastLickCount:
        csVar.lastLickCount=csVar.lickCounter
        # if the lick happens such that the minimum 
        # lick time will go over the pre time, 
        # then we advance waitTime by the minumum
        if csVar.curStateTime>(csVar.waitTime-csVar.lickWaitTime):
            csVar.waitTime = csVar.waitTime + csVar.lickWaitTime
            
def sessionCleanup(exceptionBool):

    if exceptionBool == 1:
        csVar.sesData.flush()
        print(csVar.loopCnt)
        sesNum = csVar.sesVarDict['curSession']-1

    if exceptionBool == 0:
        sesNum = csVar.sesVarDict['curSession']
    writeData(csVar.sesHDF,csVar.sesVarDict['curSession'],csVar.sesData[0:csVar.loopCnt,:],csVar.attributeLabels,csVar.attributeData)
    if csGui.useGUI==1:
        csGui.toggleTaskButtons(1)
    
    csSer.teensy.write('a0>'.encode('utf-8'))
    time.sleep(0.05)
    csSer.teensy.write('a0>'.encode('utf-8'))

    print('finished {} trials'.format(csVar.sesVarDict['trialNum']-1))
    csVar.sesVarDict['trialNum']=0

    # Update MQTT Feeds
    mqttStop(csAIO.mAIO)
    tdStamp=datetime.datetime.now().strftime("%Y_%m_%d_%H:%M:%S")
    tfStamp=datetime.datetime.now().strftime("_%Y%m%d%H%M%S")
    csGui.curNotes.append('session end: ' + tdStamp)
    if Path(csVar.sesVarDict['dirPath']).joinpath('notes').exists() == 0:
        Path(csVar.sesVarDict['dirPath']).joinpath('notes').mkdir()
    txtNotesPath = Path(csVar.sesVarDict['dirPath']).joinpath('notes').joinpath(csVar.sesVarDict['subjID'] + '_session' +\
     '{}'.format(csVar.sesVarDict['curSession']) + tfStamp + '_notes.txt')

    tempNoteString = ''
    for v in csGui.curNotes:
        if type(v) is not str:
            v = '{}'.format(v)
        tempNoteString = tempNoteString + v + '\n'
    txtNotesPath.write_text(tempNoteString)

    print('finished your session')
    csVar.sesVarDict['curSession']=csVar.sesVarDict['curSession']+1
    if csGui.useGUI==1:
        csGui.curSession_TV.set(csVar.sesVarDict['curSession'])
    csGUI.refreshPandas(csVar.sesVarDict,csVar.sensory,csVar.timing,csVar.optical,csGui.useGUI)
    csVar.sesVarDict['canQuit']=1
    csSer.flushBuffer(csSer.teensy)
    csSer.teensy.close()
    if useGUI==1:
        csGui.quitButton['text']="Quit"
        
def resolveOutputMasks():
    if csVar.c1_mask[csVar.tTrial]==2:
        csVar.c1_amp[csVar.tTrial]=0
        csVar.c2_amp[csVar.tTrial]=csVar.c2_amp[csVar.tTrial]
        # csVar.attributeData[csVar.attributeLabels.index('stimTrials')].append(1)
        # csVar.attributeData[csVar.attributeLabels.index('maskTrials')].append(0)
        print("optical --> mask trial; LED_C1: {:0.2f}V; C2 {:0.2f}V"\
            .format(5.0*(csVar.c1_amp[csVar.tTrial]/4095),5.0*(csVar.c2_amp[csVar.tTrial]/4095)))

    elif csVar.c1_mask[csVar.tTrial]!=2:
        csVar.c1_amp[csVar.tTrial]=csVar.c1_amp[csVar.tTrial]
        csVar.c2_amp[csVar.tTrial]=0
        # csVar.attributeData[csVar.attributeLabels.index('stimTrials')].append(0)
        # csVar.attributeData[csVar.attributeLabels.index('maskTrials')].append(1)
        print("optical --> stim trial; LED_C1: {:0.2f}V; C2 {:0.2f}V"\
            .format(5.0*(csVar.c1_amp[csVar.tTrial]/4095),5.0*(csVar.c2_amp[csVar.tTrial]/4095)))
            
def sendDACVariables(vTime,pTime,dTime,mTime,tTime):
    if csVar.serialVarTracker[2] == 0 and csVar.curStateTime>=vTime:
        optoVoltages = [int(csVar.c1_amp[csVar.tTrial]),int(csVar.c2_amp[csVar.tTrial])]
        csSer.sendAnalogOutValues(csSer.teensy,'v',optoVoltages)
        csVar.serialVarTracker[2] = 1
    elif csVar.serialVarTracker[3] == 0 and csVar.curStateTime>=pTime:
        optoPulseDurs = [int(csVar.c1_pulseDur[csVar.tTrial]),int(csVar.c2_pulseDur[csVar.tTrial])]
        csSer.sendAnalogOutValues(csSer.teensy,'p',optoPulseDurs)
        csVar.serialVarTracker[3] = 1
    elif csVar.serialVarTracker[4] == 0 and csVar.curStateTime>=dTime:
        optoIPIs = [int(csVar.c1_interPulseDur[csVar.tTrial]),int(csVar.c2_interPulseDur[csVar.tTrial])]
        csSer.sendAnalogOutValues(csSer.teensy,'d',optoIPIs)
        csVar.serialVarTracker[4] = 1
    elif csVar.serialVarTracker[5] == 0 and csVar.curStateTime>=mTime:
        optoPulseNum = [int(csVar.c1_pulseCount[csVar.tTrial]),int(csVar.c2_pulseCount[csVar.tTrial])]
        csSer.sendAnalogOutValues(csSer.teensy,'m',optoPulseNum)
        csVar.serialVarTracker[5] = 1
    elif csVar.serialVarTracker[6] == 0 and csVar.curStateTime>=tTime:
        optoWave = [int(csVar.c5_waveform[csVar.tTrial])]
        csSer.sendAnalogOutValues(csSer.teensy,'t',optoWave)
        csVar.serialVarTracker[6] = 1

# ~~~~~~~~~~~~~~~~~~~~
# >>> Define Tasks <<<
# ~~~~~~~~~~~~~~~~~~~~

def runDetectionTask():
    csVar.sesVarDict['taskType']='detection'
    print('made it into runDetectionTask')
    initializeTasks()
    print('initialized tasks')
    while csVar.sesVarDict['sessionOn']:
        # try to execute the task.
        try:
            updateTaskVars()
            newData = checkTeensyData()
            if newData:
                updatePlots()
                lickDetection()
                stateResolution()

                # 4) Now look at what state you are in and evaluate accordingly
                if csVar.stateSync==1:
                    if csVar.pyState == 1:
                        if csVar.sHeaders[csVar.pyState]==0:
                            genericHeader()
                            # we treat state 1 as the begining of a trial
                            # so anything we need to fix between trials ...
                            trialMaintenance()
                        setupVisualStim(10,110)
                        enforceNoLickRule()

                        # state 1 exit:
                        if csVar.curStateTime>csVar.waitTime:
                            csVar.stateSync=0
                            if csVar.contrast[csVar.tTrial]>0:
                                csVar.pyState=2
                                csSer.teensy.write('a2>'.encode('utf-8'))
                            elif csVar.contrast[csVar.tTrial]==0:
                                csVar.pyState=3
                                csSer.teensy.write('a3>'.encode('utf-8'))
                    elif csVar.pyState == 2:
                        if csVar.sHeaders[csVar.pyState]==0:
                            genericHeader()                      
         
                        if csVar.lastLick>0.02:
                            csVar.reported=1

                        if csVar.curStateTime>csVar.sesVarDict['minStim']:
                            if csVar.reported==1 or csVar.sesVarDict['shapingTrial']:
                                print("hit")
                                csVar.attributeLabels = ['stimTrials','noStimTrials','responses','binaryStim','trialDurs']
                                csVar.attributeData[csVar.attributeLabels.index('responses')].append(1)
                                csVar.attributeData[csVar.attributeLabels.index('stimTrials')].append(csVar.sesVarDict['trialNum'])
                                csVar.attributeData[csVar.attributeLabels.index('binaryStim')].append(1)
                                csVar.stateSync=0
                                csVar.pyState=4
                                csSer.teensy.write('a4>'.encode('utf-8'))
                            elif csVar.reported==0:
                                csVar.stateSync=0
                                csVar.pyState=1
                                print("miss")
                                csVar.attributeLabels = ['stimTrials','noStimTrials','responses','binaryStim','trialDurs']
                                csVar.attributeData[csVar.attributeLabels.index('responses')].append(0)
                                csVar.attributeData[csVar.attributeLabels.index('stimTrials')].append(csVar.sesVarDict['trialNum'])
                                csVar.attributeData[csVar.attributeLabels.index('binaryStim')].append(1)
                                csVar.trialSamps[1]=csVar.loopCnt
                                csVar.attributeData[csVar.attributeLabels.index('trialDurs')].append(np.diff(csVar.trialSamps)[0])
                                csSer.teensy.write('a1>'.encode('utf-8'))
                                print('miss: last trial took: {} seconds'.format(csVar.attributeData[csVar.attributeLabels.index('trialDurs')][-1]/1000))
                    elif csVar.pyState == 3:
                        if csVar.sHeaders[csVar.pyState]==0:
                            genericHeader()
         
                        if csVar.lastLick>0.005:
                            csVar.reported=1

                        if csVar.curStateTime>csVar.sesVarDict['minStim']:
                            if csVar.reported==1:
                                print("false alarm")
                                csVar.attributeLabels = ['stimTrials','noStimTrials','responses','binaryStim','trialDurs']
                                csVar.attributeData[csVar.attributeLabels.index('responses')].append(1)
                                csVar.attributeData[csVar.attributeLabels.index('noStimTrials')].append(csVar.sesVarDict['trialNum'])
                                csVar.attributeData[csVar.attributeLabels.index('binaryStim')].append(0)
                                
                                csVar.stateSync=0
                                csVar.pyState=5
                                csSer.teensy.write('a5>'.encode('utf-8'))
                                
                                if csGui.useGUI==1:
                                    csPlt.updateOutcome(stimTrials,stimResponses,noStimTrials,noStimResponses,csVar.sesVarDict['totalTrials'])
                            
                            elif csVar.reported==0:
                                # correct rejections
                                print("correct rejection")
                                csVar.attributeLabels = ['stimTrials','noStimTrials','responses','binaryStim','trialDurs']
                                csVar.attributeData[csVar.attributeLabels.index('responses')].append(0)
                                csVar.attributeData[csVar.attributeLabels.index('noStimTrials')].append(csVar.sesVarDict['trialNum'])
                                csVar.attributeData[csVar.attributeLabels.index('binaryStim')].append(0)
                                csVar.trialSamps[1]=csVar.loopCnt
                                # update sample log
                                csVar.attributeData[csVar.attributeLabels.index('trialDurs')].append(np.diff(csVar.trialSamps)[0])

                                csVar.stateSync=0
                                csVar.pyState=1
                                
                                csSer.teensy.write('a1>'.encode('utf-8'))
                                # if useGUI==1:
                                #     csPlt.updateOutcome(stimTrials,stimResponses,noStimTrials,noStimResponses,csVar.sesVarDict['totalTrials'])
                                print('correct rejection: last trial took: {} seconds'\
                                    .format(csVar.attributeData[csVar.attributeLabels.index('trialDurs')][-1]/1000))
                    elif csVar.pyState == 4:
                        if csVar.sHeaders[csVar.pyState]==0:
                            genericHeader()
                        # exit
                        if csVar.curStateTime>csVar.sesVarDict['rewardDur']:
                            csVar.trialSamps[1]=csVar.loopCnt
                            # update sample log
                            csVar.attributeData[csVar.attributeLabels.index('trialDurs')].append(np.diff(csVar.trialSamps)[0])
                            
                            csVar.stateSync=0
                            csVar.pyState=1
                            csVar.outSyncCount=0
                            csSer.teensy.write('a1>'.encode('utf-8'))
                            print('last trial took: {} seconds'.format(csVar.attributeData[csVar.attributeLabels.index('trialDurs')][-1]/1000))
                    elif csVar.pyState == 5:
                        if csVar.sHeaders[csVar.pyState]==0:
                            genericHeader()
                        # exit
                        if csVar.curStateTime>csVar.sesVarDict['toTime']:
                            csVar.trialSamps[1]=csVar.loopCnt
                            csVar.attributeData[csVar.attributeLabels.index('trialDurs')].append(np.diff(csVar.trialSamps)[0])
                            csVar.stateSync=0
                            csVar.pyState=1
                            csSer.teensy.write('a1>'.encode('utf-8'))
                            print('last trial took: {} seconds'.format(csVar.attributeData[csVar.attributeLabels.index('trialDurs')][-1]/1000))
        except:
            sessionCleanup(1)
    sessionCleanup(0)
def runTrialOptoTask():
    csVar.sesVarDict['taskType']='trialOpto'
    initializeTasks()
    while csVar.sesVarDict['sessionOn']:
        # try to execute the task.
        try:
            updateTaskVars()
            newData = checkTeensyData()
            if newData:
                updatePlots()
                stateResolution()

                # 4) Now look at what state you are in and evaluate accordingly
                if csVar.stateSync==1:
                    if csVar.pyState == 1:
                        if csVar.sHeaders[csVar.pyState]==0:
                            genericHeader()
                            # we treat state 1 as the begining of a trial
                            # so anything we need to fix between trials ...
                            trialMaintenance()
                            resolveOutputMasks()
                            try:
                                csVar.sesVarDict['useFlybackOpto'] = int(csGui.useFlybackOpto_TV.get())
                            except:
                                pass
                        # all we do in the body is update the DAC variables
                        sendDACVariables(220,320,420,520,720)

                        # state 1 exit:
                        if csVar.curStateTime>csVar.waitTime:
                            csVar.stateSync=0
                            if csVar.sesVarDict['useFlybackOpto']==1:
                                csVar.pyState=8
                                csSer.teensy.write('a8>'.encode('utf-8'))
                            elif csVar.sesVarDict['useFlybackOpto'] is not 1:
                                 csVar.pyState=7
                                 csSer.teensy.write('a7>'.encode('utf-8'))
                    elif csVar.pyState == 7:
                        if csVar.sHeaders[csVar.pyState]==0:
                            genericHeader()
                        if csVar.curStateTime>csVar.opticalStimTime[csVar.tTrial]:
                            csVar.trialSamps[1]=csVar.loopCnt
                            # update sample log
                            csVar.attributeData[csVar.attributeLabels.index('trialDurs')].append(np.diff(csVar.trialSamps)[0])
                            csVar.stateSync=0
                            csVar.pyState=1
                            csSer.teensy.write('a1>'.encode('utf-8'))

                            print('normal stim: last trial took: {} seconds'.format(csVar.attributeData[csVar.attributeLabels.index('trialDurs')][-1]/1000))
                    elif csVar.pyState == 8:
                        if csVar.sHeaders[csVar.pyState]==0:
                            genericHeader()
                        if csVar.curStateTime>csVar.sesVarDict['minStim']:
                            csVar.trialSamps[1]=csVar.loopCnt
                            # update sample log
                            csVar.attributeData[csVar.attributeLabels.index('trialDurs')].append(np.diff(csVar.trialSamps)[0])
                            csVar.stateSync=0
                            csVar.pyState=1
                            csSer.teensy.write('a1>'.encode('utf-8'))

                            print('flyback stim: last trial took: {} seconds'.format(csVar.attributeData[csVar.attributeLabels.index('trialDurs')][-1]/1000))

        except:
            sessionCleanup(1)
    sessionCleanup(0)
def runSimpleRecord():
    csVar.sesVarDict['taskType']='simpleRecording'
    initializeTasks()

    while csVar.sesVarDict['sessionOn']:
        # try to execute the task.
        try:
            updateTaskVars()
            newData = checkTeensyData()
            if newData:
                updatePlots()
                lickDetection()
                stateResolution()

                # 4) Now look at what state you are in and evaluate accordingly
                if csVar.pyState == 1 and csVar.stateSync==1:
                    if csVar.sHeaders[csVar.pyState]==0:
                        genericHeader()
                        # we treat state 1 as the begining of a trial
                        # so anything we need to fix between trials ...
                        trialMaintenance()

        except:
            sessionCleanup(1)
    sessionCleanup(0)

if useGUI==1:
    
    mainloop()
elif useGUI==0:
    if csVar.sesVarDict['taskType']=='detectionTask':
        runDetectionTask()


dd




