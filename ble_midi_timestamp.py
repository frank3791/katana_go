import time
import sys
import os
from icecream import ic

def ble_midi_timestamp():
    """
    cal timing for ble-midi
    time in ms
    use : x = ble_midi_timestamp()
    """
    result = {}
    result['time_ms_in'] = int(time.time() * 1000)
    # Modulo operation with 2**13 = 8192
    result['time_ms'] = result['time_ms_in'] % 2**13
    
    # Convert to binary and fill with zeros to 13 bits
    binary_timer = bin(result['time_ms'])[2:].zfill(13)  
    # fill byte with ble-midi requirements
    lsb_binary = "1"+binary_timer[-7:]
    msb_binary = "10"+binary_timer[:6]

    result['lsb_binary'] = lsb_binary
    result['msb_binary'] = msb_binary
    result['lsb_hex'] = hex(int(lsb_binary, 2))
    result['msb_hex'] = hex(int(msb_binary, 2))
    result['BLE_MIDI_HEADER'] = result['msb_hex'][2:]
    result['BLE_MIDI_TS'] = result['lsb_hex'][2:]
    result['binary_timer'] = binary_timer
    
    return result

if __name__ == "__main__":
    for  i in range(0,1000,1):
        ble_midi_timer = ble_midi_timestamp()
        ic(ble_midi_timer)