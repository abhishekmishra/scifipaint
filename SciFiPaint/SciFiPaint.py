import PySimpleGUI as sg

layout = [[sg.Canvas(size=(400, 300), background_color="white", k="cnv")]]

window = sg.Window(
    "SciFiPaint",
    layout,
    finalize=True,
    margins=(0, 0),
    element_padding=(0, 0),
    resizable=True,
    element_justification="c",  # center elements in the window
    enable_close_attempted_event=True,
)


def run_app():
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
            break
        print("You entered ", values[0])

    window.close()
