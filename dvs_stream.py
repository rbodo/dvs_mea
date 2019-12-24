from dv import NetworkEventInput
import time
from stg.api import STG4000

buffer_in_s=0.05 # how large is the buffer in the DLL?
capacity_in_s=.1 # how large is the buffer on the STG?

stg = STG4000()
stg.start_streaming(capacity_in_s=capacity_in_s,
                    buffer_in_s=buffer_in_s)

with NetworkEventInput(address='localhost', port=7777) as dvs_stream:
    for event in dvs_stream:
        # Should only call trigger here to start stimulus which was downloaded before. I.e. use start_stimulation()
        print(event.timestamp)
        stg.set_signal(0, amplitudes_in_mA=[0], durations_in_ms=[.1])
        time.sleep(0.5)
        stg.set_signal(0, amplitudes_in_mA=[1, -1, 0], durations_in_ms=[.1, .1, 49.7])
        time.sleep(buffer_in_s / 2)

# stg.stop_streaming()
