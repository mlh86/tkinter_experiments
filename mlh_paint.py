import tkinter as tk
import tkinter.ttk as ttk
import tkinter.colorchooser as tkcc
import tkinter.simpledialog as tksd
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkm

from collections import deque
from PIL import ImageGrab, Image
from time import sleep
import ctypes
import os
import re

C_WIDTH = 960
C_HEIGHT = 780

if os.name == 'nt':
    ctypes.windll.shcore.SetProcessDpiAwareness(2)

# For proper scrolling, need to nest a canvas inside a frame inside an outer-canvas C (as frames don't have scrollbars)

root = tk.Tk()
style = ttk.Style()
F = ttk.Frame(root)
C = tk.Canvas(root)
cframe = ttk.Frame(C)
canvas = tk.Canvas(cframe)

# Configuring top-level elements...

yscroller = ttk.Scrollbar(root, command=C.yview, orient='vertical')
xscroller = ttk.Scrollbar(root, command=C.xview, orient='horizontal')
C['xscrollcommand'] = xscroller.set
C['yscrollcommand'] = yscroller.set

F.grid(row=0,column=0,sticky='ns')
C.grid(row=0,column=1,sticky='nsew')
yscroller.grid(row=0,column=2,sticky='nsw')
xscroller.grid(row=1,column=1,sticky='ewn')

C.create_window(0,0, window=cframe, anchor='nw')
canvas.grid(row=0, column=0, sticky='nw')

root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
root['bg'] = "#dddddd"

canvas['background'] = 'white'
canvas['width'] = C_WIDTH
canvas['height'] = C_HEIGHT

C['bg'] = "#dddddd"
C['width'] = C_WIDTH
C['height'] = C_HEIGHT
C['highlightthickness'] = 0
C['scrollregion'] = (0, 0, C_WIDTH, C_HEIGHT)

F['borderwidth'] = 8
style.configure("TFrame", background="#dddddd")

def get_csize_info():
    return " (" + canvas['width'] + "x" + canvas['height'] + ")" 

# Creating left-side-column widgets...

btn_new = ttk.Button(F, text="New")
btn_open = ttk.Button(F,text="Open")
btn_save = ttk.Button(F,text="Save")
btn_saveas = ttk.Button(F,text="Save As")

btn_new.grid(row=0,column=0, pady=5)
btn_open.grid(row=1,column=0, pady=5)
btn_save.grid(row=2,column=0, pady=5)
btn_saveas.grid(row=3,column=0,pady=5)

palette = tk.Canvas(F, width=70, background="#dddddd", borderwidth=0, highlightthickness=0)
palette.grid(row=4,column=0,pady=5)


color = "black"
def setColor(newcolor):
    global color
    color = newcolor
    brush_color_btn['bg'] = color

def chooseCustomColor():
    global color
    newcolor = tkcc.askcolor(color=color)
    if newcolor[1]:
        setColor(newcolor[1])

brush_color_btn = tk.Button(F, text="    ", bg="black", command=chooseCustomColor)
brush_color_btn.grid(row=5, column=0)

brush_size = tk.StringVar(F, '1')
brush_size_optmenu = tk.OptionMenu(F, brush_size, 1,2,4,8,16)
brush_size_optmenu.grid(row=6, column=0, pady=5)
brush_size_optmenu['indicatoron'] = False
brush_size_optmenu['direction'] = 'flush'
brush_size_optmenu['width'] = 2

btn_csize = ttk.Button(F, text="W x H", width=6)
btn_csize.grid(row=7, column=0)

# Line-drawing and undo/redo logic...

histo_lines = deque(maxlen=999)
redo_lines = deque(maxlen=999)

def savePosn(event):
    global lastx, lasty
    lastx, lasty = event.x, event.y

def addLine(event):
    line_width = int(brush_size.get())
    canvas.create_line((lastx, lasty, event.x, event.y), fill=color, width=line_width)
    histo_lines.append([lastx, lasty, event.x, event.y, color, line_width])
    savePosn(event)

def addLineEndMarker(event):
    histo_lines.append(0)
    if "*" not in root.title():
        fname = current_file or "Unsaved File"
        root.title("MLH Paint - " + fname + get_csize_info() + "*")

def undo(event):
    if not histo_lines:
        return
    line_info = histo_lines.pop()
    redo_lines.append(line_info)
    while line_info:
        canvas.create_line(line_info[:4], fill='white', width=line_info[5])
        if histo_lines:
            line_info = histo_lines.pop()
            redo_lines.append(line_info)
        else:
            break

def redo(event):
    if not redo_lines:
        return
    line_info = redo_lines.pop()
    histo_lines.append(line_info)
    while line_info:
        canvas.create_line(line_info[:4], fill=line_info[4], width=line_info[5])
        if redo_lines:
            line_info = redo_lines.pop()
            histo_lines.append(line_info)
        else:
            break

def resize_canvas(event=None):
    curr_csize = str(canvas['width']) + "x" + str(canvas['height'])
    new_csize_str = tksd.askstring("Specify Canvas Size", "Use the WxH format\t\t\t", initialvalue=curr_csize)
    if not new_csize_str:
        return
    if not re.match("\d{2,4}x\d{2,4}$", new_csize_str):
        tkm.showwarning("Invalid Size Specified", "Please enter a width and height between\n10 and 9999 using the WxH format.")
    else:
        canvas['width'] = new_csize_str.split('x')[0]
        canvas['height'] = new_csize_str.split('x')[1]
        C.configure(scrollregion = (0, 0, canvas['width'], canvas['height']))

# File-handling Logic...

img = None
current_file = ""
root.title("MLH Paint - Unsaved File" + get_csize_info())

def new_file(evt=None):
    global current_file, histo_lines
    if "*" in root.title():
        save_first = tkm.askyesnocancel("Save Current File?", 
            "Would you like to save changes to the current file first?")
        if save_first and not current_file:
            file_saved = save_file_as()
            if not file_saved:
                return
        elif save_first:
            save_canvas_to_png_file(current_file)
        elif save_first == None:
            return
    canvas.delete('all')
    histo_lines = []
    current_file = ""
    root.title("MLH Paint - Unsaved File" + get_csize_info())


def open_file(evt=None):
    global img
    global current_file
    if "*" in root.title():
        save_first = tkm.askyesnocancel("Save Current File?",
            "Would you like to save changes to the current file first?")
        if save_first and not current_file:
            file_saved = save_file_as()
            if not file_saved:
                return
            sleep(0.2)
        elif save_first:
            save_canvas_to_png_file(current_file)
        elif save_first == None:
            return
    fpath = tkfd.askopenfilename(filetypes=[("PNG Files", "*.png")])
    if not fpath:
        return False
    # Add try-except to handle file-open errors...
    img = tk.PhotoImage(file=fpath)
    canvas.delete('all')
    canvas['width'] = img.width()
    canvas['height'] = img.height()
    canvas.create_image(0, 0, image=img, anchor='nw')
    current_file = fpath
    root.title("MLH Paint - " + fpath + get_csize_info())

def save_canvas_to_png_file(filepath):
    temp_tk = tk.Toplevel(root)
    temp_tk.title("Saving file...")
    temp_tk.geometry("")
    temp_pb = ttk.Progressbar(temp_tk)
    temp_pb.pack()
    temp_tk.transient(root)
    temp_tk.geometry("+%d+%d" % (400, 200))
    temp_pb.step(25)
    root.update()
    canvas.postscript(file = "temp_pycanvas.eps", pagewidth=canvas['width'], pageheight=canvas['height'])
    temp_pb.step(25)
    root.update()
    img = Image.open("temp_pycanvas.eps")
    img.save(filepath, 'png')
    temp_pb.step(25)
    root.update()
    img.close()
    os.remove("temp_pycanvas.eps")
    temp_tk.destroy()

def save_file_as(evt=None):
    global current_file
    fpath = tkfd.asksaveasfilename(defaultextension=".png",
                filetypes=[("PNG Files","*.png")])
    if not fpath:
        return False
    save_canvas_to_png_file(fpath)
    root.title("MLH Paint - " + fpath + get_csize_info())
    current_file = fpath
    return True

def save_file(evt=None):
    if current_file:
        save_canvas_to_png_file(current_file)
        root.title("MLH Paint - " + current_file + get_csize_info())
    else:
        save_file_as()


# Command-bindings...

canvas.bind("<Button-1>", savePosn)
canvas.bind("<B1-Motion>", addLine)
canvas.bind("<ButtonRelease-1>",addLineEndMarker)

btn_new['command'] = new_file
btn_open['command'] = open_file
btn_save['command'] = save_file
btn_saveas['command'] = save_file_as
btn_csize['command'] = resize_canvas

root.bind("<Control-Shift-S>", save_file_as)
root.bind("<Control-s>", save_file)
root.bind("<Control-o>", open_file)
root.bind("<Control-n>", new_file)
root.bind("<Control-z>", undo)
root.bind("<Control-Shift-Z>", redo)

# Assigning color-values to palette buttons...

colors = ['black','white','darkgray','lightgray','maroon','brown',
          'red','pink','orange','gold','yellow','light yellow',
          'green','lime','dark turquoise','light sky blue','blue4',
          'blue','purple','blue violet']
top = 5
left_odd = 5
left_even = 40

for i in range(len(colors)):
    if i % 2:
        id = palette.create_rectangle((left_odd, top, left_odd+25, top+25), fill=colors[i])
        palette.tag_bind(id, "<Button-1>", lambda event, brush_color=colors[i]: setColor(brush_color))
        top += 30
    else:
        id = palette.create_rectangle((left_even, top, left_even+25, top+25), fill=colors[i])
        palette.tag_bind(id, "<Button-1>", lambda event, brush_color=colors[i]: setColor(brush_color))

root.mainloop()
