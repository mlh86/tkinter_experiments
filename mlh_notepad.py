# A basic text-editor

import tkinter as tk
import tkinter.ttk as ttk
import tkinter.filedialog as tkfd
import tkinter.messagebox as tkm
from time import sleep

root = tk.Tk()
T = tk.Text(undo=True)
F = ttk.Frame()

F.grid(row=0,column=0,sticky='ns')
T.grid(row=0,column=1,sticky='nsew')
root.columnconfigure(1, minsize=800, weight=1)
root.rowconfigure(0, minsize=600, weight=1)

btn_new = ttk.Button(F, text="New")
btn_open = ttk.Button(F,text="Open")
btn_save = ttk.Button(F,text="Save")
btn_saveas = ttk.Button(F,text="Save As")

btn_new.grid(row=0,column=0, pady=5)
btn_open.grid(row=1,column=0, pady=5)
btn_save.grid(row=2,column=0, pady=5)
btn_saveas.grid(row=3,column=0,pady=5)
F['borderwidth'] = 8

current_file = ""
base_title = "MLH Text Editor"
root.title(base_title + " - Unsaved")

def new_file(evt=None):
    global current_file
    if T.count(1.0,'end')[0] > 1 and T.edit_modified():
        save_first = tkm.askyesnocancel("Save Current File?", 
            "Would you like to save changes to the current file first?")
        if save_first and not current_file:
            file_saved = save_file_as()
            if not file_saved:
                return
        elif save_first:
            save_current_file()
        elif save_first == None:
            return
    T.delete(1.0,'end')
    T.edit_reset()
    root.title(base_title + " - Unsaved")
    current_file = ""

def open_file(evt=None):
    global current_file
    if T.count(1.0,'end')[0] > 1 and T.edit_modified():
        save_first = tkm.askyesnocancel("Save Current File?",
            "Would you like to save changes to the current file first?")
        if save_first and not current_file:
            file_saved = save_file_as()
            if not file_saved:
                return
            sleep(0.2)
        elif save_first:
            save_current_file()
        elif save_first == None:
            return
    fpath = tkfd.askopenfilename(
                filetypes=[("Text Files", "*.txt"),("All Files", "*")])
    if not fpath:
        return False
    with open(fpath, 'r') as f:
        T.delete(1.0,'end')
        text=f.read()
        T.insert('end', text)
        T.edit_reset()
        root.title(base_title + " - " + f.name)
        current_file = fpath

def save_current_file(evt=None):
    with open(current_file, 'w') as output_file:
        text = T.get(1.0,'end')
        output_file.write(text)

def save_file_as(evt=None):
    global current_file
    fpath = tkfd.asksaveasfilename(defaultextension=".txt",
                filetypes=[("Text Files","*.txt"),("All Files","*.*")])
    if not fpath:
        return False
    with open(fpath, "w") as output_file:
        text = T.get(1.0,'end')
        output_file.write(text)
    root.title(base_title + " - " + fpath)
    current_file = fpath
    return True

def save_file(evt=None):
    if current_file:
        save_current_file()
    else:
        save_file_as()

def select_all(evt=None):
    T.tag_add('sel',1.0,'end')
    return 'break'

def do_undo(evt=None):
    T.edit_undo()

def do_redo(evt=None):
    T.edit_redo()

btn_new['command'] = new_file
btn_open['command'] = open_file
btn_save['command'] = save_file
btn_saveas['command'] = save_file_as

T.bind("<Control-a>", select_all)
T.bind("<Control-Shift-S>", save_file_as)
T.bind("<Control-s>", save_file)
T.bind("<Control-o>", open_file)
T.bind("<Control-n>", new_file)
T.bind("<Control-z>", do_undo)
T.bind("<Control-Shift-Z>", do_redo)

root.mainloop()
