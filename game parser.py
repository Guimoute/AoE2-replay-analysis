# -*- coding: utf-8 -*-
"""
Author: Guimoute.
"""

# Imports.
import matplotlib as mpl
import matplotlib.pyplot as plt
import mgz, mgz.header, mgz.body # <3 https://github.com/happyleavesaoc/aoc-mgz
import numpy as  np
import os

# Constants.
PATH = os.path.join(os.path.dirname(__file__), "test.aoe2record")

# Open a game and get information.
def get_operations(path) -> list:

    with open(path, "rb") as data:

        end_of_file = os.fstat(data.fileno()).st_size
        _ = mgz.header.parse_stream(data)
        _ = mgz.body.meta.parse_stream(data)

        operations = []
        while data.tell() < end_of_file:
            operation = mgz.body.operation.parse_stream(data)
            operations.append(operation)

        return operations



def get_player_actions(operations:list, player_id:int) -> list:

    return [ope for ope in operations if ope.type == "action" and getattr(ope.action, "player_id", None) == player_id]



def operations_per_time_increment(operations:list, dt:int) -> list:
    """TODO: use the `sync` operation to convert game ticks to game seconds."""

    slices = [[]]
    time_threshold = dt

    for operation in operations:
        if operation.start <= time_threshold:
            slices[-1].append(operation)
        else:
            time_threshold += dt
            slices.append([])
            slices[-1].append(operation)

    return slices



def player_eapm_over_time_increment(operations, player_id:int, dt:int) -> (list, list):

    actions = get_player_actions(operations, player_id)
    actions = operations_per_time_increment(actions, dt)
    local_eapms = [len(subactions) for subactions in actions]
    last_time:int = actions[-1][-1].start
    times = np.linspace(0, last_time, len(actions))
    return times, local_eapms



def sliding_average(array, n):
    # Coursety of Alleo: https://stackoverflow.com/a/27681394/9282844
    cumsum = np.cumsum(np.insert(array, 0, 0))
    return (cumsum[n:] - cumsum[:-n]) / float(n)



# APM(time) graph.
fig, ax = plt.subplots()
fig.show()
operations = get_operations(PATH)

#%%
# ax.clear()
dt = 20000
n = 4
smoothing_function = lambda a: sliding_average(a, 2*n)

for player in (1, 2):
    color = {1: "red", 2: "blue"}[player]

    # Plot the raw data.
    t, eapm = player_eapm_over_time_increment(operations, player, dt)
    ax.scatter(t, eapm, color=color, alpha=0.15)

    # Plot smoothed data.
        # Pad the borders before smoothing data.
    t = np.insert(t, 0, [0]*n)
    t = np.insert(t, -1, [t[-1]]*n)
    eapm = np.pad(eapm, n, mode="constant", constant_values=0)

    t, eapm = map(smoothing_function, (t, eapm))
    ax.plot(t, eapm, color=color, alpha=1.0)

# Legend and labels.
c = "grey"
handles = (mpl.lines.Line2D([], [], color=c, lw=4),
           mpl.lines.Line2D([], [], color=c, lw=0, marker="o", markersize=8, alpha=0.3))
labels = (f"Smooth data ({n=})",
          "Raw data")
ax.legend(handles, labels, loc="upper left", bbox_to_anchor=(1.03, 1), numpoints=3)
fig.tight_layout()
ax.set_xlabel("Game ticks")
ax.set_ylabel(f"Actions per time section\n({dt} ticks)")
ax.set_title("APM(time)")

fig.canvas.draw()

