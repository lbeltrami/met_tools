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