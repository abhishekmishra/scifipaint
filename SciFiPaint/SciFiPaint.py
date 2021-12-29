import PySimpleGUI as sg
from SciFiCmdr import commander, register_command, register_handler
from SciFiCmdr import is_command, run_command, cmdhandler
import tkinter as tk
import os
import sys
import argparse
from platformdirs import PlatformDirs
from PIL import ImageGrab
from PIL import Image, ImageTk
from pathlib import Path
import logging

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

IMAGE_FILE_TYPES = [("JPG Files", "*.jpg *.jpeg"), ("PNG Files", "*.png")]

__version__ = "0.0.1"


def do(command_name, **kwargs):
    w = kwargs.get("window", window)
    e = kwargs.get("event", None)
    v = kwargs.get("values", None)
    run_command(command_name, window=w, event=e, values=v, **kwargs)


def save_element_as_file(element, filename):
    """
    Saves any element as an image file.  Element needs to have an underlyiong Widget available (almost if not all of them do)
    :param element: The element to save
    :param filename: The filename to save to. The extension of the filename determines the format (jpg, png, gif, ?)
    """
    widget = element.Widget
    box = (
        widget.winfo_rootx(),
        widget.winfo_rooty(),
        widget.winfo_rootx() + widget.winfo_width(),
        widget.winfo_rooty() + widget.winfo_height(),
    )
    grab = ImageGrab.grab(bbox=box)
    grab.save(filename)


def save_element_ps_method(element, filename):
    canvas = element.Widget

    outf = Path(filename)
    ps_outf = outf.with_suffix(".eps")

    # save postscipt image
    canvas.postscript(file=ps_outf)
    # use PIL to convert to PNG
    img = Image.open(ps_outf)
    img.save(outf)
    os.remove(ps_outf)


class Painter:
    def __init__(self):
        self.dirty = False
        self.filepath = None
        self.pendown = False
        self.cx = 0
        self.cy = 0

    def set_filepath(self, fpath):
        self.filepath = fpath
        if os.path.isfile(self.filepath):
            # see https://stackoverflow.com/a/26479906/9483968
            # if image is not stored, it is garbage collected before
            # use in the canvas
            self.img = ImageTk.PhotoImage(Image.open(self.filepath))
            canvas = window["cnv"].Widget
            canvas.create_image(0, 0, image=self.img, anchor="nw")
        self.dirty = False

    def newfile(self):
        self.dirty = False
        self.filepath = None
        self.pendown = False
        self.cx = 0
        self.cy = 0

    def savefile(self):
        try:
            if self.filepath:
                save_element_ps_method(window["cnv"], self.filepath)
                self.dirty = False
            else:
                raise ValueError("filepath is not set.")
        except Exception as e:
            print("fatal error: ", e)


painter = Painter()


@cmdhandler()
def cnv_penmove(**kwargs):
    cnv = kwargs["window"]["cnv"]
    painter.pendown = True
    painter.cx = cnv.user_bind_event.x
    painter.cy = cnv.user_bind_event.y
    painter.dirty = True
    if painter.pendown:
        dia = 6
        r = dia / 2
        cnv.tk_canvas.create_oval(
            painter.cx - r,
            painter.cy - r,
            painter.cx + r,
            painter.cy + r,
            fill="red",
            outline="blue",
        )


@cmdhandler()
def cnv_penmove(**kwargs):
    cnv = kwargs["window"]["cnv"]
    painter.cx = cnv.user_bind_event.x
    painter.cy = cnv.user_bind_event.y
    painter.dirty = True
    if painter.pendown:
        dia = 6
        r = dia / 2
        cnv.tk_canvas.create_oval(
            painter.cx - r,
            painter.cy - r,
            painter.cx + r,
            painter.cy + r,
            fill="red",
            outline="blue",
        )


@cmdhandler()
def cnv_penup(**kwargs):
    cnv = kwargs["window"]["cnv"]
    painter.pendown = False
    painter.cx = cnv.user_bind_event.x
    painter.cy = cnv.user_bind_event.y
    painter.dirty = True


@cmdhandler()
def new_file(**kwargs):
    if not run_command("confirm_save", **kwargs):
        return
    painter.newfile()


@cmdhandler()
def confirm_save(**kwargs):
    if painter.dirty:
        save_continue_msg = """
            The current file has changes, save and continue?
            """
        choice, _ = sg.Window(
            "Save current file?",
            [
                [sg.T(save_continue_msg)],
                [sg.Yes(s=10), sg.No(s=10), sg.Cancel(s=10)],
            ],
            disable_close=True,
        ).read(close=True)

        if choice == "Yes":
            print("save file and continue")
            run_command("save_file", **kwargs)
            return True
        elif choice == "No":
            print("continue without saving the file")
            return True
        else:
            print("abort operation")
            return False
    else:
        return True


@cmdhandler()
def open_file(filename=None, **kwargs):
    if not run_command("confirm_save", **kwargs):
        return
    if filename is None:
        filename = choose_file_to_open(kwargs["window"].TKroot)
    if filename:
        painter.set_filepath(filename)
        return filename


def choose_file_to_open(rootwin):
    intial_folder = None
    filename = None
    if sg.running_mac():
        filename = tk.filedialog.askopenfilename(initialdir=intial_folder)
    else:
        filename = tk.filedialog.askopenfilename(
            filetypes=IMAGE_FILE_TYPES,
            initialdir=intial_folder,
            parent=rootwin,
        )
    return filename


def choose_file_to_save(rootwin):
    intial_folder = None
    filename = tk.filedialog.asksaveasfilename(
        filetypes=IMAGE_FILE_TYPES,
        initialdir=intial_folder,
        parent=rootwin,
    )
    return filename


@cmdhandler()
def save_file(**kwargs):
    if painter.filepath is None:
        painter.filepath = choose_file_to_save(kwargs["window"].TKroot)
    if painter.filepath:
        painter.savefile()


@cmdhandler()
def toggle_fullscreen(**kwargs):
    if "window" in kwargs.keys():
        w = kwargs["window"]
        if w and w.maximized:
            w.normal()
        else:
            w.maximize()


@cmdhandler()
def commandbar(**kwargs):
    cmd = commander()
    if cmd:
        run_command(cmd, **kwargs)
    return cmd


@cmdhandler()
def window_title(**kwargs):
    fmtstr = "{program_name} {program_version} - '{file_name}' {dirty_status}"
    title_text = fmtstr.format(
        program_name="SciFiTide",
        program_version="0.0.1",
        file_name=painter.filepath if painter.filepath else "Untitled",
        dirty_status="*" if painter.dirty else "✔",
    )
    kwargs["window"].set_title(title_text)


def get_config():
    pd = PlatformDirs("scifipaint")
    config_dir = pd.user_config_dir
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    sys.path.append(config_dir)
    main_config_file = os.path.join(config_dir, "stfucfg.py")
    if not os.path.exists(main_config_file):
        print(main_config_file, "does not exist")
    else:
        __import__("stfucfg")


def get_args():
    arg_parser = argparse.ArgumentParser(
        "scifipaint: minimal paint application"
    )
    arg_parser.add_argument(
        "filename", help="path to the file to open", nargs="?"
    )
    args = arg_parser.parse_args()
    return args


layout = [[sg.Canvas(size=(1000, 800), background_color="white", k="cnv")]]

window = sg.Window(
    "SciFiPaint",
    layout,
    finalize=True,
    margins=(0, 0),
    element_padding=(0, 0),
    resizable=False,
    element_justification="c",  # center elements in the window
    enable_close_attempted_event=True,
)

window.bind("<Control-n>", "new_file")
window.bind("<Control-o>", "open_file")
window.bind("<Control-s>", "save_file")
window.bind("<F11>", "toggle_fullscreen")
window.bind("<Control-P>", "commandbar")

window["cnv"].bind("<ButtonPress-1>", "_pendown")
window["cnv"].bind("<ButtonRelease-1>", "_penup")
window["cnv"].bind("<B1-Motion>", "_penmove")

window["cnv"].set_focus(force=True)


def run_app():
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
            if not run_command(
                "confirm_save", window=window, event=event, values=values
            ):
                continue
            else:
                break

        if is_command(event):
            run_command(event, window=window, event=event, values=values)

        # print(event, values, window["cnv"].user_bind_event)

    window.close()
