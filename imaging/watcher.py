"""
Script to plot new images in a watched folder/file, indicating whether they are saturated or not.

The Leica software appears to hold the images in memory and will write them to disk when requested
(not clear that these are in a tmp folder/file). A user could therefore capture many images before
a file is written out.

Workflow is therefore that user takes images and saves as they go, which updates the file. The script
periodically (~1min) reads the file and plots the latest set.

run with:
py "C:\\Program Files\\python_scripts\\watcher.py" "Z:\\Image Facility User Data\\User\\Folder"
"""

import glob
import sys
import os
import time
import numpy as np
import matplotlib.pyplot as plt
from readlif.reader import LifFile


def get_meta(et, name, i):
    """Return the channel metadata given a element tree of all input data.

    Unclear what settings actually correspond to what we want, but can
    explore by viewing xml tree and comparing to what LAS X gives.
    """
    # print(f'meta for {name}')
    meta = {'name': name}
    data = et.find(f".//Element[@Name='{name}']")

    # wavelength (not all channels have line)
    # x = data.findall(".//Attachment[@Name='HardwareSetting']/ATLConfocalSettingDefinition//DetectionReferenceLine")
    # wav_int = []
    # for x_ in x:
    #     wav_int.append(x_.attrib['LaserWavelength'])
    # meta['wav'] = wav_int[i]

    # dye for each channel
    dyes = []
    x = data.findall(".//ChannelDescription/ChannelProperty")
    for j in x:
        for k in j:
            if k.text == 'DyeName':
                dyes.append(j[1].text)

    meta['dye'] = dyes[i]

    # timestamps
    x = data.find(".//TimeStampList")
    times = [float.fromhex(a) for a in x.text.strip().split(' ')]
    meta['time'] = times[i]

    return meta


def get_last_image(file):
    f = LifFile(file)

    times = []
    for i in range(f.num_images):
        im = f.get_image(i)
        meta = get_meta(f.xml_root, im.info['name'], 0)
        times.append(meta['time'])

    return np.argmax(times)


def plot(file, fig, max=255):
    """Plot channels of a LIF file image, with histograms."""

    # open the file and get frames
    # could reduce image sizes if necessary
    last_i = get_last_image(file)
    lif = LifFile(file)
    im = lif.get_image(last_i)
    print(f"plotting file: {file}, {im.info['name']}")
    ims = []
    meta = []
    for i, ch in enumerate(im.get_iter_c()):
        ims.append(ch)
        meta.append(get_meta(lif.xml_root, im.info['name'], i))

    # clear the last figure and set up the grid
    fig.clf()
    grid = fig.add_gridspec(2, int(np.ceil(len(ims)/2)), hspace=0.2)

    # loop over the images and plot them plus their histograms
    for i in range(len(ims)):
        inner = grid[i].subgridspec(2, 1, height_ratios=[1,0.3], hspace=0)
        axs = inner.subplots()
        data = np.asarray(ims[i]).flatten()
        ls = [max-1, max+1]
        axs[0].imshow(ims[i], vmax=np.percentile(data, 99), cmap='Greys')
        axs[0].contour(ims[i], levels=ls, colors='red')
        axs[0].set_title(meta[i]['dye'])

        _ = axs[1].hist(data, bins=100, log=True)
        axs[1].text(max, np.max(_[0]), f'{np.sum(data==max)/len(data)*100:3.2f}% sat',
                    horizontalalignment='right', verticalalignment='top')
        axs[1].set_xlim(0, max*1.05)
        axs[0].set(xticks=[], yticks=[])
        axs[1].set(yticks=[])

    fig.suptitle(f"{f}/{im.info['name']}")
    fig.subplots_adjust(top=0.92, bottom=0.05)
    # fig.tight_layout()
    plt.pause(1)   # runs the GUI long enough to make and show the figure


if __name__ == '__main__':

    print(f'Running watcher on folder: {sys.argv[1]}')
    print('')
    print('Hit Ctrl-c to stop it.')

    fig = plt.figure(figsize=(10, 6))

    last_mtime = 0
    while True:

        fs = np.array(glob.glob(f'{sys.argv[1]}/*lif'))

        mtimes = np.array([])
        for f in fs:
            mtimes = np.append(mtimes, os.path.getmtime(f))

        srt = np.argsort(mtimes)
        fs = fs[srt]
        mtimes = mtimes[srt]

        if mtimes[-1] != last_mtime:
            print(f'Showing: {fs[-1]}')
            plot(fs[-1], fig)

        last_mtime = mtimes[-1]

        time.sleep(10)
