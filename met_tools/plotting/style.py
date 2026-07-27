def plot_style():
    """
    Apply standard style for all plots:
    - Seaborn theme
    - Font sizes
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    sns.set_theme(style="whitegrid", palette="deep")

    plt.rc('axes', titlesize=16)   # axis title
    plt.rc('axes', labelsize=16)   # axis labels
    plt.rc('xtick', labelsize=12)  # X tick labels
    plt.rc('ytick', labelsize=12)  # Y tick labels
    plt.rc('legend', fontsize=16)  # legend
    plt.rc('figure', titlesize=20) # figure title



def rain_colormap():
    """
    Discrete colormap suitable for rainfall fields, inspired by Capecchi et al. (2022).

    Colors:
    white -> cyan -> light blue -> dark blue -> magenta -> orange -> red -> dark red
    """

    from matplotlib.colors import ListedColormap

    colors = [
        "#FFFFFF",  # white
        "#22DDE0",  # cyan
        "#1F84F0",  # light blue
        "#1212FF",  # dark blue
        "#F020F0",  # magenta
        "#FF8800",  # orange
        "#FF0000",  # red
        "#C00000",  # dark red
    ]

    return ListedColormap(colors, name="rain_colormap")
