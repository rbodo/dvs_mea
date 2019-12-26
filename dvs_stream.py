import time
from dv import NetworkEventInput
from stg.api import STG4000

use_streaming_mode = False

stg = STG4000()

pulse_amplitude = [-1, 1, 0]
pulse_duration = [0.1, 0.1, 1]

num_rows = 8
num_columns = 8
xmax = 128
ymax = 128
ds_x = xmax // num_columns
ds_y = ymax // num_rows

roi_list_mea = [(0, 1, 0, 1), (7, 8, 7, 8)]  # (y_min, y_max, x_min, x_max)
roi_list = [(y_min * ds_y, y_max * ds_y, x_min * ds_x, x_max * ds_x)
            for y_min, y_max, x_min, x_max in roi_list_mea]

to_skip = {(0, 0), (0, num_columns - 1), (num_rows - 1, 0),
           (num_rows - 1, num_columns - 1)}

address_to_index_map = []
for c in range(num_columns):
    for r in range(num_rows):
        if (r, c) in to_skip:
            continue
        address_to_index_map.append((c, r))


def get_electrode_address(y, x, roi_list):

    for y_min, y_max, x_min, x_max in roi_list:
        if y_min <= y < y_max and x_min <= x < x_max:
            return y_min, y_max, x_min, x_max


# In streaming mode, implement LIF-like behavior. Each event increases the
# stimulation voltage by a bit. Once a threshold is crossed, the voltage is
# reset. Always decaying.
if use_streaming_mode:

    buffer_in_s = 0.001  # how large is the buffer in the DLL?
    capacity_in_s = 0.1  # how large is the buffer on the STG?
    stg.start_streaming(capacity_in_s=capacity_in_s,
                        buffer_in_s=buffer_in_s)

    with NetworkEventInput(address='localhost', port=7777) as dvs_stream:
        while True:  # dvs_stream.is_open()
            event = dvs_stream.__next__()
            if event is None:  # try: dvs_stream.__next__(); except IsEmpty
                for roi in roi_list_mea:
                    channel_index = address_to_index_map.index((roi[2],
                                                                roi[0]))
                    stg.set_signal(channel_index, [0], [buffer_in_s * 1000])  # Instead of buffer size, should maybe only have length of stimulus (if appended instead of overwritten)
            else:
                t = event.timestamp
                x = event.x
                y = event.y

                addr = get_electrode_address(y, x, roi_list)
                if addr is None:
                    continue

                y_mea, _, x_mea, _ = addr
                channel_index = address_to_index_map.index((x, y))

                # Test whether this overwrites or appends to previous calls.
                stg.set_signal(channel_index, [-1, 1, 0], [0.1, 0.1, buffer_in_s * 1000 - 0.2])
                stg.sleep(buffer_in_s / 2)
                stg.set_signal(channel_index, [0], [buffer_in_s * 1000])

    stg.stop_streaming()

else:
    for roi in roi_list_mea:
        channel_index = address_to_index_map.index((roi[2], roi[0]))
        stg.download(channel_index, pulse_amplitude, pulse_duration)
    with NetworkEventInput(address='localhost', port=7777) as dvs_stream:
        for event in dvs_stream:

            t = event.timestamp
            x = event.x
            y = event.y

            addr = get_electrode_address(y, x, roi_list)
            if addr is None:
                continue

            y_mea, _, x_mea, _ = addr
            channel_index = address_to_index_map.index((x, y))
            stg.start_stimulation([channel_index])
