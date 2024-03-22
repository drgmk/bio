"""Script to plot new images in a watched folder,
giving an idea of whether they are saturated or not."""

import glob
import sys
import os
import time
from readlif.reader import LifFile
import numpy as np
import matplotlib.pyplot as plt


def plot(file, fig, max=255):
    """Plot panels of a LIF file, with histograms."""

    # open the file and get frames
    # could reduce image sizes if necessary
    lif = LifFile(file)
    ims = []
    meta = []
    for i, im in enumerate(lif.get_iter_image()):
        ims.append(im.get_frame())
        meta.append(im.info['name'])

    # clear the last figure and set up the grid
    fig.clf()
    grid = fig.add_gridspec(2, int(len(ims)//2), hspace=0.2)

    # loop over the images and plot them plus their histograms
    for i in range(len(ims)):
        inner = grid[i].subgridspec(2, 1, height_ratios=[1,0.3], hspace=0)
        axs = inner.subplots()
        data = np.asarray(ims[i]).flatten()
        ls = [max-1, max+1]
        axs[0].imshow(ims[i], vmax=np.percentile(data, 99), cmap='Greys')
        axs[0].contour(ims[i], levels=ls, colors='red')
        axs[0].set_title(meta[i])

        _ = axs[1].hist(data, bins=100, log=True)
        axs[1].text(max, np.max(_[0]), f'{np.sum(data==max)/len(data)*100:3.2f}% sat',
                    horizontalalignment='right', verticalalignment='top')
        axs[1].set_xlim(0, max*1.05)
        axs[0].set(xticks=[], yticks=[])
        axs[1].set(yticks=[])

    fig.suptitle(f)
    fig.subplots_adjust(top=0.92, bottom=0.05)
    # fig.tight_layout()
    plt.pause(1)   # runs the GUI long enough to make and show the figure


if __name__ == '__main__':

    print(f'Running watcher on folder: {sys.argv[1]}')
    print('')
    print('Hit Ctrl-c to stop it.')

    fig = plt.figure(figsize=(10, 6))

    last_file = ''
    while True:

        time.sleep(1)

        fs = np.array(glob.glob(f'{sys.argv[1]}/*lif'))

        mtimes = []
        for f in fs:
            mtimes.append(os.path.getmtime(f))

        srt = np.argsort(mtimes)
        fs = fs[srt]

        if fs[-1] != last_file:
            print(f'Showing: {fs[-1]}')
            plot(fs[-1], fig)

        last_file = fs[-1]
