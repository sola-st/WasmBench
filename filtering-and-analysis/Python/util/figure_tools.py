import matplotlib as mpl
import matplotlib.pyplot as plt


# Set font to Fira Sans to be compatible with the other figures
def set_font_fira_sans():
    # see https://stackoverflow.com/questions/35668219/how-to-set-up-a-custom-font-with-custom-path-to-matplotlib-global-font
    font_paths = ['fonts-for-figures']
    font_files = mpl.font_manager.findSystemFonts(fontpaths=font_paths)
    # print(font_files)
    font_list = mpl.font_manager.createFontList(font_files)
    # print(font_list)
    mpl.font_manager.fontManager.ttflist.extend(font_list)
    mpl.rcParams['font.family'] = 'Fira Sans'
    mpl.rcParams['font.weight'] = 'regular'


def set_font_size(points):
    mpl.rcParams["font.size"] = str(points)


def scale_current_figure(sizefactor):
    # see https://stackoverflow.com/questions/332289/how-do-you-change-the-size-of-figures-drawn-with-matplotlib
    # Get current size
    fig_size = plt.gcf().get_size_inches()
    # Modify the current size by the factor
    plt.gcf().set_size_inches(sizefactor * fig_size)
