# -*- coding: utf-8 -*-
"""
Created on Sun Nov  8 14:37:21 2020

@author: Louis Beal
louis.j.beal@gmail.com
"""

import cv2, os, sys, imageio

from PIL import Image, ImageDraw, ImageTk

import numpy as np
import tkinter as tk

from tkinter import filedialog

class GUI:
    
    def __init__(self, master):
        self.master = master
        
        self.stats = {}
        
        self.avg_img = None
        
        self.sync()
        self.buildGUI()
        
        
    def sync(self):
        
        #settings, dict
        #name: [tk var type, default value]
        self.settingspath = "settings.opt"
        self.settings = {
            "path":[tk.StringVar(),"/"],
            "outpath":[tk.StringVar(),"/"],
            "targetfps":[tk.IntVar(),6],
            "scaling":[tk.IntVar(),3],
            "clip_lft":[tk.IntVar(),0],
            "clip_top":[tk.IntVar(),0],
            "clip_rgt":[tk.IntVar(),1000],
            "clip_bot":[tk.IntVar(),1000],
            "clip_start":[tk.DoubleVar(),0],
            "clip_end":[tk.DoubleVar(),0]}             
        
        self.load()
        self.save()
        
    def load(self):
        print("loading settings")
        #sync with settings file
        if not os.path.isfile(self.settingspath):
            #no settings detected, create with defaults
            with open(self.settingspath, "w+") as o:
                for var in self.settings.keys():
                    
                    val = self.settings[var][1]
                    
                    o.write("{},{}\n".format(var,val))
                    
        else:
            with open(self.settingspath, "r") as o:
                file = o.readlines()
                
            loaded = {}
            for opt in file:
                line = opt.split(",")
                var = line[0].strip()
                val = line[1].strip()
                
                loaded[var] = val
                
            
            for var in self.settings.keys():        
                if var in loaded.keys():
                    self.settings[var][0].set(loaded[var])
                else:
                    print("!!! {} missing, defaulting".format(var))
                    self.settings[var][0].set(self.settings[var][1])
                    
    def save(self):
        print("saving settings")        
        with open(self.settingspath, "w+") as o:
            for var in self.settings.keys():      
                val = self.settings[var][0].get()
                o.write("{},{}\n".format(var,val))
            
    def s(self, var, val = None, debug = False):
        #short function to handle inividual settings
        #call with (name, value) to set setting
        #call without value to just fetch setting
        
        if val == None:
            if debug:
                print("!!! self.s: mode: read: ")
                print(var)
                print(self.settings[var][0].get())
                
            return(self.settings[var][0].get())
        else:
            if debug:
                print("!!! self.s: mode: write: ")
                print(var)
                print(self.settings[var][0].get())
                print("==>")
                print(val)
                
            self.settings[var][0].set(val)
            self.save()
        
    def mp4init_new(self):
        path = filedialog.askopenfilename(initialdir = self.s("path"), title = "Select file",filetypes = (("mp4","*.mp4"),("all files","*.*")))

        if path != "":
        
            self.s("path", path)
            
            self.mp4Init()
        
    def mp4Init(self):
        
        self.updateStatus("creating average frame")
        
        path = self.s("path")
        
        self.save()
        
        if path == "/":
            self.mp4init_new()
            
        if path.split(".")[-1] != "mp4":
            self.mp4init_new()
        
        print("loading vid file from " + path)
        
        cap = cv2.VideoCapture(path)
        
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        nFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        self.showVidStats({"height":[h,"px"],
                           "width":[w,"px"],
                           "frames":[nFrames,""],
                           "fps":[fps,"/s"],
                           "length":[round(nFrames/fps,3),"s"]
                           })
        
        self.stats["h"] = h
        self.stats["w"] = w
        self.stats["nFrames"] = nFrames
        self.stats["fps"] = fps
        
        dec = 5
        avg_img = np.zeros([h,w,3]).astype(np.float)
        
        self.lowres = [] #storage for small images
        
        for i in range(nFrames):
            
            self.updateStatus("frame {} of {}".format(i+1,nFrames))
            
            ret, frame = cap.read()
            
            imageRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            temp = Image.fromarray(imageRGB).convert("L")            
            temp = temp.resize([round(temp.size[0]/4),round(temp.size[1]/4)])
            
            self.lowres.append(temp)
            
            if i % dec == 0:
                avg_img = avg_img + imageRGB*(dec/nFrames)
        
        cap.release()
        
        avg_img = np.array(np.round(avg_img),dtype=np.uint8)
        
        self.avg_img = Image.fromarray(avg_img, mode = 'RGB')
        
        self.update_image()
        
        self.updateStatus()
        
        
    def mp4toNewGif(self):
        path = filedialog.asksaveasfilename(initialdir = self.s("path"), title = "Select file",filetypes = (("gif","*.gif"),("all files","*.*")))
        
        #print("DIALOGBOX PATH ")
        #print(path)
        
            
        if path != "":
            
            if "." not in path:
                path = path + ".gif"
                
            self.s("outpath", path, debug = True)
            
            self.mp4toGif(new=True)
        
    def mp4toGif(self,new=False):
        
        self.updateStatus("converting to .gif")
        
        path = self.s("path")
        outpath = self.s("outpath")
        
        cap = cv2.VideoCapture(path)
        
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        nFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        self.stats["h"] = h
        self.stats["w"] = w
        self.stats["nFrames"] = nFrames
        self.stats["fps"] = fps
        
        
        target_fps = self.s("targetfps")
        scaling = self.s("scaling")
        
        clip_lft = self.s("clip_lft")
        clip_top = self.s("clip_top")
        clip_rgt = self.s("clip_rgt")
        clip_bot = self.s("clip_bot")
        
        startFrame = round(self.s("clip_start")*self.stats["fps"])
        endFrame = round(nFrames - self.s("clip_end")*self.stats["fps"])

        clipping = [clip_lft,clip_top,clip_rgt,clip_bot]
        
        if not new:
            outpath = "/".join(path.split("/")[:-1])+"/test.gif"
        
        
        self.s("outpath",outpath)
        self.save()
        
        print("creating gif at " + outpath)
        
        frameNo = list(range(nFrames))[startFrame:endFrame]
        
        
        segment = round(self.stats["fps"]/target_fps)
        
        target_w = round(self.stats["w"]/scaling)
        target_h = round(self.stats["h"]/scaling)
        
        
        
        seq = []
        for i in range(nFrames):
            
            self.updateStatus("frame {} of {}".format(i+1,nFrames))
            
            ret, frame = cap.read()
                            
            if i % segment == 0 and i in frameNo:
                
                imageRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                img = Image.fromarray(imageRGB, mode = "RGB")
            
                img = img.resize([target_w,target_h],resample=3)
                
                img = img.crop([round(c/scaling) for c in clipping])
                
                
                seq.append(img)
        
        seq[0].save(outpath, save_all=True, append_images=seq, loop=0)

        seq = []

        self.updateStatus()
        
    def update_box(self, args = None):
        self.save()
        
        self.update_image()
        
    def update_image(self,args=None):
        
        imgtype = 0
        if args in [0,1,2]:
            imgtype = args
            
        
        try:
            self.avg_canvas.delete(self.canvasimg)
        except:
            pass
              
        w = self.avg_canvas.winfo_width()
        h = self.avg_canvas.winfo_height()
        
        #print("canvas size: {}x{}".format(w,h))
        
        if self.avg_img != None:
        
            x_scale = w/self.avg_img.size[0]
            y_scale = h/self.avg_img.size[1]
            
            #print("udpate agv img")
            self.tempimg = self.avg_img.resize([w,h])
            
            if imgtype == 1:
                #print("udpate first img")
                n = round(self.s("clip_start")*self.stats["fps"])
                self.tempimg = self.lowres[n].resize([w,h])
            elif imgtype == 2:
                #print("udpate last img")
                n = round(self.stats["nFrames"] - self.s("clip_end")*self.stats["fps"])
                self.tempimg = self.lowres[n].resize([w,h])
        
            self.canvasimg = ImageTk.PhotoImage(self.tempimg)
            
            self.avg_canvas.create_image((w/2,h/2),image=self.canvasimg)
            
            clip_lft = self.s("clip_lft")*x_scale
            clip_top = self.s("clip_top")*y_scale
            clip_rgt = self.s("clip_rgt")*x_scale
            clip_bot = self.s("clip_bot")*y_scale

            self.avg_canvas.create_rectangle([clip_lft,clip_top,clip_rgt,clip_bot], fill="",outline="red")
            
            xsize = round((self.s("clip_rgt") - self.s("clip_lft"))/self.s("scaling"))
            ysize = round((self.s("clip_bot") - self.s("clip_top"))/self.s("scaling"))
            
            self.size_xlabel.configure(text = "{}px".format(xsize))
            self.size_xlabel.update()
            self.size_ylabel.configure(text = "{}px".format(ysize))
            self.size_ylabel.update()
        
    def updateStatus(self, updatetext=None):
        #update lower status bar
        #pass with no args to reset
        if updatetext != None:
            self.statusbar.configure(text = updatetext)
        else:
            self.statusbar.configure(text = "ready")
            
        self.statusbar.update()
        
    def showVidStats(self,infodict=None):
        #display statistics about loaded video file
        if infodict == None:
            self.vidstats.configure(text = "Video Statistics:\nNone")
            
        else:
            statstext = "Video Statistics:"
            
            for stat in infodict.keys():
                statstext = statstext + "\n{}: {} {}".format(stat,infodict[stat][0],infodict[stat][1])
                
            self.vidstats.configure(text = statstext)
            
        self.vidstats.update()
        
    def buildGUI(self):
        master = self.master
        
        master.title("mp4 to gif")
        
        self.lframe = tk.Frame(master,borderwidth=2,relief="solid")
        self.lframe.grid(row=0,column=0,sticky="NESW")
        
        
        #video statistics
        self.statsframe = tk.Frame(master,borderwidth=2,relief="solid")
        self.statsframe.grid(row=1,column=0,sticky="NESW")
        
        self.vidstats = tk.Label(self.statsframe, text = "Video Statistics:\nNone")
        self.vidstats.pack(side="bottom",expand=True,fill="both")
        
        
        #processing status
        self.status = tk.Frame(master,borderwidth=2,relief="solid")
        self.status.grid(row=2,column=0,sticky="NESW")
        
        self.statusbar = tk.Label(self.status, text = "ready")
        self.statusbar.pack(side="bottom",expand=True,fill="both")
        
        
        #image frame
        self.rframe = tk.Frame(master,borderwidth=2,relief="solid")
        self.rframe.grid(row=0,column=1,rowspan=10,sticky="NESW")
        
        
        
        master.grid_columnconfigure(1, weight=1)
        master.grid_rowconfigure(0, weight=1)
        
        
        self.load_button = tk.Button(self.lframe, text="Open mp4", command=self.mp4init_new)
        self.load_button.grid(row=0,column=0)
        self.load_button = tk.Button(self.lframe, text="(previous)", command=self.mp4Init)
        self.load_button.grid(row=0,column=1)
        
        tk.Label(self.lframe).grid(row=1)
        
        self.clip_x1 = tk.Entry(self.lframe, textvar = self.settings["clip_lft"][0])
        self.clip_y1 = tk.Entry(self.lframe, textvar = self.settings["clip_top"][0])
        self.clip_x2 = tk.Entry(self.lframe, textvar = self.settings["clip_rgt"][0])
        self.clip_y2 = tk.Entry(self.lframe, textvar = self.settings["clip_bot"][0])
        
        tk.Label(self.lframe,text="x").grid(row=2,column=1)
        tk.Label(self.lframe,text="y").grid(row=2,column=2)
        tk.Label(self.lframe,text="1").grid(row=3,column=0)
        tk.Label(self.lframe,text="2").grid(row=4,column=0)
        self.clip_x1.grid(row = 3,column=1)
        self.clip_y1.grid(row = 3,column=2)
        self.clip_x2.grid(row = 4,column=1)
        self.clip_y2.grid(row = 4,column=2)
        
        xsize = round((self.s("clip_rgt") - self.s("clip_lft"))/self.s("scaling"))
        ysize = round((self.s("clip_bot") - self.s("clip_top"))/self.s("scaling"))
        
        self.size_xlabel = tk.Label(self.lframe, text="{}px".format(xsize))
        self.size_xlabel.grid(row = 5, column = 1)
        
        self.size_ylabel = tk.Label(self.lframe, text="{}px".format(ysize))
        self.size_ylabel.grid(row = 5, column = 2)
        
        tk.Label(self.lframe).grid(row = 6)
        
        self.scale_label = tk.Label(self.lframe, text = "Scale Factor")
        self.scale_entry = tk.Entry(self.lframe, textvar = self.settings["scaling"][0])
        
        scalefactor = round(100/int(self.s("scaling")),3)
        self.scale_pc = tk.Label(self.lframe, text = "{}%".format(scalefactor))
        self.fps_entry = tk.Entry(self.lframe, textvar = self.settings["targetfps"][0])
        self.fps_label = tk.Label(self.lframe, text = "fps output")
        
        self.scale_entry.grid(row = 7, column = 1)
        self.scale_label.grid(row = 7, column = 0)
        self.scale_pc.grid(row = 7, column = 2)
        self.fps_entry.grid(row = 8, column = 1)
        self.fps_label.grid(row = 8, column = 0)
        
        
        tk.Label(self.lframe).grid(row = 10)
        
        self.starttrim_label = tk.Label(self.lframe, text = "start trim")
        self.endtrim_label = tk.Label(self.lframe, text = "start trim")
        
        self.starttrim_entry = tk.Entry(self.lframe, textvar = self.settings["clip_start"][0])
        self.endtrim_entry = tk.Entry(self.lframe, textvar = self.settings["clip_end"][0])
        
        tk.Label(self.lframe, text = "time (s): ").grid(row = 12, column = 0)
        
        self.starttrim_label.grid(row = 11, column = 1)
        self.endtrim_label.grid(row = 11, column = 2)
        self.starttrim_entry.grid(row = 12, column = 1)
        self.endtrim_entry.grid(row = 12, column = 2)
        
        self.firstincframe = tk.Frame(self.lframe)
        self.lastincframe = tk.Frame(self.lframe)
        
        self.firstincframe.grid(row = 13, column = 1)
        self.lastincframe.grid(row = 13, column = 2)
        
        self.firstinc = incrementer(self.firstincframe, value = self.settings["clip_start"][0], binding = [self.update_image,1])
        self.lastinc = incrementer(self.lastincframe, value = self.settings["clip_end"][0], binding = [self.update_image,2])
        
        tk.Label(self.lframe).grid(row = 14)
        
        self.displayfstt = tk.Button(self.lframe, text = "first frame", command = lambda:self.update_image(1))
        self.displayfend = tk.Button(self.lframe, text = "last frame", command = lambda:self.update_image(2))
        self.showavgimg = tk.Button(self.lframe, text = "avg frame", command = lambda:self.update_image(0))
        
        self.showavgimg.grid(row = 15, column = 0)
        self.displayfstt.grid(row = 15, column = 1)
        self.displayfend.grid(row = 15, column = 2)
        
        
        
        
        tk.Label(self.lframe).grid(row = 19)
        
        self.create_button = tk.Button(self.lframe, text="create gif", command=self.mp4toNewGif)
        self.create_button.grid(row=20,column=0)
        
        self.create_button = tk.Button(self.lframe, text="at test.gif", command=self.mp4toGif)
        self.create_button.grid(row=20,column=1)
        
        self.avg_canvas = tk.Canvas(self.rframe,borderwidth=2,relief="solid")
        self.avg_canvas.pack(fill="both",expand="true")
        
        self.avg_canvas.bind("<Configure>", self.update_image)
        
        self.clip_x1.bind("<Key>",self.update_box)
        self.clip_y1.bind("<Key>",self.update_box)
        self.clip_x2.bind("<Key>",self.update_box)
        self.clip_y2.bind("<Key>",self.update_box)
        
        self.scale_entry.bind("<Key>",self.update_scale)
        

    def update_scale(self, args = None):
        scalefactor = round(100/int(self.s("scaling")),3)
        self.scale_pc.configure(text = "{}%".format(scalefactor))
        self.scale_pc.update()
        
        self.save()
    
class incrementer:
    
    def __init__(self,master,value,inc=None,binding=None):
        
        self.inc = tk.DoubleVar()
        
        self.value = value
        
        self.binding = binding[0]
        self.bindingargs = binding[1]
        
        if inc == None:
            self.inc.set(0.1)
        else:
            self.inc.set(inc)
        
        master.columnconfigure(1, weight = 1)
        
        self.plusbtn = tk.Button(master, text = "+", command = self.plus)
        self.downbtn = tk.Button(master, text = "-", command = self.down)
        self.amount = tk.Entry(master, textvariable = self.inc, width = 5)
        
        self.downbtn.grid(row = 0, column = 0, sticky = "NEWS")
        self.amount.grid(row = 0, column = 1, sticky = "NEWS")
        self.plusbtn.grid(row = 0, column = 2, sticky = "NEWS")
        """
        if binding != None:
            self.downbtn.bind("<ButtonRelease-1>", binding)
            self.plusbtn.bind("<ButtonRelease-1>", binding)"""
        
    def plus(self):
        
        self.value.set(round(self.value.get() + self.inc.get(),3))
        if self.binding != None:
            self.binding(self.bindingargs)
            
    def down(self):
        
        self.value.set(round(self.value.get() - self.inc.get(),3))
        if self.binding != None:
            self.binding(self.bindingargs)

if __name__ == "__main__":
    root = tk.Tk()
    my_gui = GUI(root)
    root.mainloop()