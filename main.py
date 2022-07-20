import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import MaxNLocator
import os
import pandas as pd
import numpy as np
from numpy import unravel_index
import PySimpleGUI as sg


# ------ FUNCTIONS ------
def draw_figure(canvas, figure):    # Function for drawing the figure and link it to canvas
    figureCanvasAgg = FigureCanvasTkAgg(figure, canvas)
    figureCanvasAgg.draw()
    figureCanvasAgg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figureCanvasAgg


def plot_data():    # Plot a 2D line plot
    if value['-TIME-']:
        data[value['-X-']] = pd.to_datetime(data[value['-X-']])
    else:
        data[value['-X-']] = data[value['-X-']].astype(float)

    data[value['-Y-']] = data[value['-Y-']].astype(float)
    ax = data.plot(value['-X-'], value['-Y-'], figsize=fSize)
    ax.set_xlabel(value['-X-'])
    ax.set_ylabel(value['-Y-'])
    # ax.plot(x, y)
    ax.xaxis.set_major_locator(MaxNLocator(7))
    ax.yaxis.set_major_locator(MaxNLocator(7))
    ax.grid()
    fig = ax.get_figure()
    return fig, ax  # Return graph handlers


# def multi_plot():


def plot_spectrum(data):

    spectre = pd.read_csv(data, sep='\t', header=27, engine='python', decimal='.') # read the raw data without the header
    fic_header = pd.read_csv(data, sep='\t', header=None, nrows=26, engine='python', decimal='.') # read the header values
    fic_header.columns = ["Name", "value"] # rename the columns for the header

    time_step = 1 / np.float64(fic_header.value[1]) # compute time step from sampling rate
    step_numb = spectre.shape[1] - 2
    X_axis = np.array(spectre.iloc[:, 1]) # x axis is the first column of the raw data
    #MQ = make_MQ(abs(X_axis), np.float64(fic_header.value[21]), COEFB0, COEFB1, COEFB2, COEFB4)
    Y_axis = np.arange(0, step_numb * time_step, time_step) # create a list to provide the time of aquisition

    spectre_image = spectre.drop(spectre.columns[0], axis=1)
    spectre_image = spectre_image.drop(spectre_image.columns[0], axis=1)
    spectre_image = spectre_image.to_numpy()

    indexes = unravel_index(spectre_image.argmax(), spectre_image.shape) # find max of the 2D array with coordinates

    # Generate the plot
    fig, (ax1, ax2, ax3) = plt.subplots(3, figsize=[12, 12], constrained_layout=True)

    cmap = ax1.pcolormesh(Y_axis, X_axis, spectre_image)
    fig.colorbar(cmap, ax=ax1)
    ax1.axhline(y=X_axis[indexes[0]], color='b', linestyle='-')
    ax1.axvline(x=Y_axis[indexes[1]], color='r', linestyle='-')
    ax1.set_xlabel('Times [s]')
    ax1.set_ylabel('M/Q [arb. units]')
    #title = f + ', Pinj = ' + fic_header.value[8] + ', Pext = ' + fic_header.value[9] + ', HT = ' + str(
    #    float(fic_header.value[21]))
    #ax1.set_title(title)

    toto = spectre_image[:, indexes[1]]
    toto[toto < 0] = 0
    ax2.plot(X_axis, toto, color='r')
    ax2.set_xlim(min(X_axis), max(X_axis))
    ax2.set_ylim(min(toto), max(toto) + max(toto) * 0.2)
    ax2.set_xlabel('M/Q [arb. units]')
    ax2.set_ylabel('Intensity [mA]')


    toto2 = spectre_image[indexes[0], :]
    ax3.set_xlim(min(Y_axis), max(Y_axis))
    ax3.plot(Y_axis, toto2, color='b')
    #ax3.plot(data["TIME (s)"], data["daq_U_Anode (Vdaq)"].values / 500, label='U_Anode (Vdaq)/10', color='k')
    ax3.set_xlabel('Times [s]')
    ax3.set_ylabel('Intensity [mA]')

    return fig, ax1, ax2, ax3  # Return graph handlers


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
plotted = False
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

spectrum_plot_tab = [
    [sg.T('Spectrum', size=(5, 1)),
     sg.Button('Plot Spectrum', key='-SPECPLOT-')]
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
     sg.TabGroup([[sg.Tab('Plot 2D', plot2D_tab, key='-PLOT2D-'), sg.Tab('Multi Plot', multi_plot_tab, key='-MULTIPLOT-'), sg.Tab('Spectrum Plot', spectrum_plot_tab, key='-SPECTRUM-')]])],

    [sg.Frame('Data', layout=[], visible=False, key='-DATAFRAME-')]
]

layout = [
    [sg.TabGroup([[sg.Tab('Main', main_tab_layout, key='-MAINTAB-')]], key='-MAIN-')]
]

sg.theme('DarkBlue')
window = sg.Window('Data visualization', layout, size=(wW, wH), finalize=True)  # Create main window

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
            
            if '-DATA-' in window.AllKeysDict:
                window['-DATA-'].update(visible=False)
                window['-DELETE-'].update(visible=False)
                window['-DATA-'].Widget.master.pack_forget()
                window['-DELETE-'].Widget.master.pack_forget()

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
            i = 0
            while i < ys:
                key = ''.join(['-YMULTI', str(i), '-'])
                window[key](values=headings)
                i += 1

        except ValueError:
            window['-OUT-'].update('ValueError')
        except FileNotFoundError:
            window['-OUT-'].update('File not found')
        except KeyError:
            window['-OUT-'].update('Wrong Separator')

    if event == '-PLOT-':   # Plot the selected data
        fig, ax = plot_data()   # Get handles of the plot figure
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
        if ys <= 4:
            window.extend_layout(window['-MULTIPLOT-'], new_y(ys))
            key = ''.join(['-YMULTI', str(ys), '-'])
            window[key](values=headings)
            ys += 1
        else:
            window['-OUT-']('There are enough Y\'s')

    if event == '-SPECPLOT-':   # Plot the selected data
        fig, ax1, ax2, ax3 = plot_spectrum(file)   # Get handles of the plot figure
        tabName = 'Spectrum'
        if f'-TAB-{tabName}-' not in window.AllKeysDict:
            window['-MAIN-'].add_tab(sg.Tab(f'{tabName}', layout=tab(tabName), key=f'-TAB-{tabName}-'))   # Add a new tab for the new fig
            figAgg = draw_figure(window[f'-GRAPH-{tabName}-'].TKCanvas, fig)  # Link the fig to the canvas
            figs[tabName] = fig
        else:
            window[f'-TAB-{tabName}-'](visible=True)
        window[f'-TAB-{tabName}-'].select()  # Select the newly added tab