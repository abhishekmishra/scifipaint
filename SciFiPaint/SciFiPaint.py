import PySimpleGUI as sg
from SciFiCmdr import commander, register_command, register_handler
from SciFiCmdr import is_command, get_handlers
import tkinter as tk
import os
import sys
import argparse
from platformdirs import PlatformDirs

IMAGE_FILE_TYPES = [("JPG Files", "*.jpg *.jpeg"), ("PNG Files", "*.png")]

__version__ = "0.0.1"

register_command("text_undo")
register_command("text_redo")
register_command("new_file")
register_command("confirm_save")
register_command("open_file")
register_command("save_file")
register_command("toggle_fullscreen")
register_command("commandbar")
register_command("window_title")
register_command("about")
register_command("cnvpendown")
register_command("cnvpenmove")
register_command("cnvpenup")


def run_command(command_name, window=None, event=None, values=None, **kwargs):
    """
    Run command given by command_name(str) with arguments window, event,
    and values from the pysimplegui window

    Parameters:
        command_name (str): name of the command to run.
            program will look for method '%command_name%'
            in global scope to run.

        window, event, values: the objects from pysimplegui window
            these will be passed as-is to the command function if found.

    Returns:
        Return value of executed command function.

    Throws:
        NameError if cmd_%command_name% not found.
    """
    if is_command(command_name) is not None:
        cmd_handlers = get_handlers(command_name)
        ret = None
        for cmdfn in cmd_handlers:
            ret = cmdfn(window=window, event=event, values=values, **kwargs)
        return ret
    else:
        NameError(command_name + " is not a command")


def do(command_name, **kwargs):
    w = kwargs.get("window", window)
    e = kwargs.get("event", None)
    v = kwargs.get("values", None)
    run_command(command_name, window=w, event=e, values=v, **kwargs)


# see https://stackoverflow.com/a/54030205/9483968
def sfthandler(command=None):
    def wrap(f):
        if command is not None and is_command(command):
            register_handler(command, f)
        else:
            raise KeyError(command, "is not a registered command")
        return f

    return wrap


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
            raise ValueError("not implemented")
            # with open(self.filepath, "r") as f:
            #     self.content = f.read()
        else:
            self.content = ""
        self.dirty = False

    def newfile(self):
        self.dirty = False
        self.filepath = None
        self.pendown = False
        self.cx = 0
        self.cy = 0

    def savefile(self):
        if self.filepath:
            raise ValueError("not implemented yet")
            # with open(self.filepath, "w") as f:
            #     f.write(self.content)
            # self.dirty = False
        else:
            raise ValueError("filepath is not set.")


painter = Painter()


@sfthandler(command="cnvpendown")
def cnvpenmove(**kwargs):
    cnv = kwargs["window"]["cnv"]
    painter.pendown = True
    painter.cx = cnv.user_bind_event.x
    painter.cy = cnv.user_bind_event.y
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


@sfthandler(command="cnvpenmove")
def cnvpenmove(**kwargs):
    cnv = kwargs["window"]["cnv"]
    painter.cx = cnv.user_bind_event.x
    painter.cy = cnv.user_bind_event.y
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


@sfthandler(command="cnvpenup")
def cnvpenup(**kwargs):
    cnv = kwargs["window"]["cnv"]
    painter.pendown = False
    painter.cx = cnv.user_bind_event.x
    painter.cy = cnv.user_bind_event.y


@sfthandler(command="new_file")
def new_file(**kwargs):
    if not run_command("confirm_save", **kwargs):
        return
    painter.newfile()
    kwargs["window"]["ed"].update(value=painter.content)
    # reset the undo stack, and clear the edit modified flag
    kwargs["window"]["ed"].Widget.edit_reset()
    kwargs["window"]["ed"].Widget.edit_modified(False)


@sfthandler(command="confirm_save")
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


@sfthandler(command="open_file")
def open_file(filename=None, **kwargs):
    if not run_command("confirm_save", **kwargs):
        return
    if filename is None:
        intial_folder = None
        if sg.running_mac():
            filename = tk.filedialog.askopenfilename(
                initialdir=intial_folder
            )  # show the 'get file' dialog box
        else:
            filename = tk.filedialog.askopenfilename(
                filetypes=IMAGE_FILE_TYPES,
                initialdir=intial_folder,
                parent=kwargs["window"].TKroot,
            )  # show the 'get file' dialog box
    if filename:
        painter.set_filepath(filename)
        kwargs["window"]["ed"].update(value=painter.content)
        # reset the undo stack, and clear the edit modified flag
        kwargs["window"]["ed"].Widget.edit_reset()
        kwargs["window"]["ed"].Widget.edit_modified(False)

        return filename


@sfthandler(command="save_file")
def save_file(**kwargs):
    if painter.filepath:
        painter.savefile()
    else:
        sg.popup_ok("need to ask the user for filename")


@sfthandler(command="toggle_fullscreen")
def toggle_fullscreen(**kwargs):
    if "window" in kwargs.keys():
        w = kwargs["window"]
        if w and w.maximized:
            w.normal()
        else:
            w.maximize()


@sfthandler(command="commandbar")
def commandbar(**kwargs):
    cmd = commander()
    if cmd:
        run_command(cmd, **kwargs)
    return cmd


@sfthandler(command="window_title")
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

window["cnv"].bind("<ButtonPress-1>", "pendown")
window["cnv"].bind("<ButtonRelease-1>", "penup")
window["cnv"].bind("<B1-Motion>", "penmove")

window["cnv"].set_focus(force=True)


def run_app():
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
            break

        if is_command(event):
            run_command(event, window, event, values)

        run_command("window_title", window, None, None)

        print(event, values, window['cnv'].user_bind_event)

    window.close()
