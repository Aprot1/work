import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator
import os
import pandas as pd
import PySimpleGUI as sg


# ------ FUNCTIONS ------
def draw_figure(canvas, figure):    # Function for drawing the figure and link it to canvas
    figureCanvasAgg = FigureCanvasTkAgg(figure, canvas)
    figureCanvasAgg.draw()
    figureCanvasAgg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figureCanvasAgg


def plot_data():    # Plot a 2D line plot
    x = value['-X-']
    y = value['-Y-']
    if value['-TIME-']:
        data[x] = pd.to_datetime(data[x])
    else:
        data[x] = data[x].astype(float)

    data[y] = data[y].astype(float)
    ax = data.plot(x, y, figsize=fSize)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.xaxis.set_major_locator(MaxNLocator(7))
    ax.yaxis.set_major_locator(MaxNLocator(7))
    ax.grid()
    fig = ax.get_figure()
    return fig  # Return graph handlers


def multi_plot():
    x = value['-XMULTI-']
    if value['-TIMEMULTI-']:
        data[x] = pd.to_datetime(data[x])
    else:
        data[x] = data[x].astype(float)

    plt.cla()
    plt.clf()
    ax = plt.gca()
    for i in yList:
        data.plot(x, value[i], figsize=fSize, ax=ax)
    ax.set_xlabel(x)
    ax.xaxis.set_major_locator(MaxNLocator(7))
    ax.yaxis.set_major_locator(MaxNLocator(7))
    ax.grid()
    fig = ax.get_figure()
    return fig  # Return graph handlers


def delete_figure_agg(figure_agg):  # Delete fig to clear the canvas
    figure_agg.get_tk_widget().forget()
    plt.close('all')


def tab(name):  # Create and return the new tab layout
    lay = [
        [sg.Graph(canvas_size=cSize, graph_bottom_left=(0, 0), graph_top_right=cSize,
                  key=f'-GRAPH-{name}-')],

        [sg.Input(f'{name}', key=f'-SAVENAME-{name}-'),
         sg.Button('Save plot', key=f'-SPLOT-{name}-'),
         sg.Button('Close tab', key=f'-CLOSET-{name}-')]
    ]
    return lay


def new_y(y):
    key = ''.join(['-YMULTI', str(y), '-'])
    txt = ''.join(['Y Axis ', str(y)])
    yList.append(key)
    return [[sg.T(txt), sg.Combo([], size=(9, 1), key=key, enable_events=True)]]


# ------ VARIABLES ------
px = 1/plt.rcParams['figure.dpi']   # Unit conversion for plot size (fcking matplotlib works in INCHES...)
wW, wH = sg.Window.get_screen_size()    # Get screen size to size the elements
wH = wH - 70
figs = {}
sepDict = {';': ';', ',': ',', '[TAB]': '\x09', '[SPACE]': '\t'}  # Dict for separators
cSize = (wW, wH)  # Canvas size
fSize = ((wW-20)*px, (wH-100)*px)  # Fig size
dSize = (wW/3, wH)   # Data table size
headings = []
yList = ['-YMULTI0-']
ys = 1

# ------ LAYOUT ------
plot2D_tab = [
    [sg.T('X Axis', size=(5, 1)),
     sg.Combo([], size=(9, 1), key='-X-'),
     sg.Checkbox('Time ?', key='-TIME-')],

    [sg.T('Y Axis', size=(5, 1)),
     sg.Combo([], size=(9, 1), key='-Y-'),
     sg.Button('Plot', key='-PLOT-')]
]

multi_plot_tab = [
    [sg.T('X Axis', size=(5, 1)),
     sg.Combo([], size=(9, 1), key='-XMULTI-'),
     sg.Checkbox('Time ?', key='-TIMEMULTI-')],

    [sg.T('Y Axis', size=(5, 1)),
     sg.Combo([], size=(9, 1), key='-YMULTI0-'),
     sg.Button('+', key='-ADDY-'),
     sg.Button('Plot', key='-MPLOT-')]
]

file_frame = [
    [sg.Input(enable_events=True, key='-PATH-'),
     sg.FileBrowse()],

    [sg.T('Separator'),
     sg.Combo(list(sepDict.keys()), default_value=';', size=7, key='-SEPARATOR-'),
     sg.T('Header'),
     sg.Input('0', size=(3, 1), key='-HEADER-'),
     sg.T('Decimal'),
     sg.Input('.', size=(3, 1), key='-DEC-'),
     sg.Button('Load', key='-LOAD-')]
]

# MAIN TAB LAYOUT
main_tab_layout = [
    [sg.Frame('', layout=file_frame),
     sg.Frame('Preview', layout=[[sg.Multiline(size=(50, 4), disabled=True, key='-OUT-')]]),
     sg.TabGroup([[sg.Tab('Plot 2D', plot2D_tab, key='-PLOT2D-'), sg.Tab('Multi Plot', multi_plot_tab, key='-MULTIPLOT-')]])],

    [sg.Frame('Data', layout=[], visible=False, key='-DATAFRAME-')]
]

layout = [
    [sg.TabGroup([[sg.Tab('Main', main_tab_layout, key='-MAINTAB-')]], key='-MAIN-')]
]

sg.theme('DarkBlue')
window = sg.Window('Data visualization', layout, size=(wW, wH))  # Create main window

# ------ MAIN WINDOW LOOP ------
while True:
    event, value = window.read()    # Scan window for events

    if event == sg.WIN_CLOSED:  # Quit X button
        break

    if event == '-PATH-':   # If file input is filled, try to read the file to display a preview
        try:
            file = value['-PATH-']
            file = open(file)
            prev = file.read()
            file.close()
            window['-OUT-'](prev)    # Update preview with raw file
        except FileNotFoundError:
            pass

    if event == '-LOAD-':   # Load Button
        try:
            window['-OUT-']('')
            file = value['-PATH-']
            ext = file.split('.')[-1]   # Find extension

            if ext == 'csv' or 'txt':   # Different methods to open file depending on extension
                sep = sepDict[value['-SEPARATOR-']]
                header = int(value['-HEADER-'])
                dec = value['-DEC-']
                data = pd.read_csv(file, sep=sep, header=header, decimal=dec, encoding='latin-1')

            values = data.values.tolist()   # Table element takes lists for value & headings
            headings = data.columns.tolist()
            f = file.split('/')  # Get file name without the whole path
            f = ''.join(['Data : ', f[-1]])
            window['-DATAFRAME-'](f)  # Change frame name
            
            # if '-DATA-' in window.AllKeysDict:
            #     window['-DATA-'].update(visible=False)
            #     window['-DELETE-'].update(visible=False)
            #     window['-DATA-'].Widget.master.pack_forget()
            #     window['-DELETE-'].Widget.master.pack_forget()

            window.extend_layout(window['-DATAFRAME-'],
                                 [
                                     [sg.Table(values=values, headings=headings, justification='right',
                                               num_rows=30, vertical_scroll_only=False, expand_x=False,
                                               key='-DATA-')],
                                     [sg.Button('Delete Selected', key='-DELETE-')]
                                 ])

            window['-DATAFRAME-'](visible=True)  # Make -DATAFRAME- element visible
            window['-X-'](values=headings)  # Update combo boxes with heading values
            window['-Y-'](values=headings)
            window['-XMULTI-'](values=headings)
            for i in yList:
                window[i](values=headings)

        except ValueError:
            window['-OUT-'].update('ValueError')
        except FileNotFoundError:
            window['-OUT-'].update('File not found')
        except KeyError:
            window['-OUT-'].update('Wrong Separator')

    if event == '-PLOT-':   # Plot the selected data
        fig = plot_data()   # Get handles of the plot figure
        tabName = ''.join([value['-Y-'], ' = f(', value['-X-'], ')'])
        if f'-TAB-{tabName}-' not in window.AllKeysDict:
            window['-MAIN-'].add_tab(sg.Tab(f'{tabName}', layout=tab(tabName), key=f'-TAB-{tabName}-'))   # Add a new tab for the new fig
            figAgg = draw_figure(window[f'-GRAPH-{tabName}-'].TKCanvas, fig)  # Link the fig to the canvas
            figs[tabName] = fig
        else:
            window[f'-TAB-{tabName}-'](visible=True)
        window[f'-TAB-{tabName}-'].select()  # Select the newly added tab

    if event == '-DELETE-':  # Delete the selected data rows
        data.drop(value['-DATA-'], inplace=True)    # Delete data
        data.reset_index(drop=True, inplace=True)   # Reset index
        values = data.values.tolist()
        window['-DATA-'](values=values)  # Update the -DATA- table

    if event.startswith('-SPLOT-'):    # Save plot button, the name depends on the tab it is in
        folder = sg.popup_get_folder('On which folder to save ?')
        if folder is not None:
            if not os.path.isdir(folder):   # If folder doesn't exist, create it
                os.mkdir(folder)
            tabName = event.split('SPLOT')[-1]  # get the tab name
            tabName = tabName[1:-1]
            fig = figs[tabName]
            fileName = value[f'-SAVENAME-{tabName}-']
            fileName = ''.join([folder, '/', fileName, '.png'])
            fig.savefig(fileName)   # save plot with given path/name

    if event.startswith('-CLOSET-'):    # Delete tab button, the tab name depends on the tab it is in
        tabName = event.split('CLOSET')[-1]
        tabName = tabName[1:-1]
        window[f'-TAB-{tabName}-'](visible=False)

    if event == '-ADDY-':   # Add a Y Combo to choose multiple data to plot
        if ys <= 4:  # Limit to 4 total data to plot
            window.extend_layout(window['-MULTIPLOT-'], new_y(ys))  # add a Y combo box
            key = ''.join(['-YMULTI', str(ys), '-'])
            window[key](values=headings)
            ys += 1
        else:
            window['-OUT-']('There are enough Y\'s')

    if event == '-MPLOT-':  # TO plot multiple data on the same graph
        fig = multi_plot()  # Get handles of the plot figure
        tabName = ''.join(['f(', value['-XMULTI-'], ')'])
        if f'-TAB-{tabName}-' not in window.AllKeysDict:
            window['-MAIN-'].add_tab(sg.Tab(f'{tabName}', layout=tab(tabName), key=f'-TAB-{tabName}-'))  # Add a new tab for the new fig
            figAgg = draw_figure(window[f'-GRAPH-{tabName}-'].TKCanvas, fig)  # Link the fig to the canvas
            figs[tabName] = fig
        else:
            window[f'-TAB-{tabName}-'](visible=True)
        window[f'-TAB-{tabName}-'].select()  # Select the newly added tab