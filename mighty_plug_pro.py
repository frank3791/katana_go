import sys
import os
import asyncio
from bleak import BleakScanner, BleakError, BleakClient
from icecream import ic

import ble_midi_timestamp

class MightyPlugPro:
    def __init__(self):
        self.dev_name = "NUX NMP-03"
        self.BLE_MIDI_HEADER = "94"
        self.BLE_MIDI_TIMESTAMP = "f4"
        self.STX = "f0"
        self.NUX = "43"
        self.MODEL_ID = "5870"
        self.RQ1 = '11'
        self.DT1 = '12'
        self.EOX = "f7"
        self.DATA = "7f0001000000"

        self.ble_address = "cb:4e:fd:31:35:62"
        BLE_MODEL_NBR_UUID_MIDI_SERVICE = "03B80E5A-EDE8-4B33-A751-6CE34EC4C700"
        BLE_MODEL_NBR_UUID_MIDI_DATA_IO = "7772E5DB-3868-4112-A1A9-F2669D106BF3"
        self.UUID = BLE_MODEL_NBR_UUID_MIDI_DATA_IO

    def send_midi_hex(self, msg = "80 80 c0 01"):
        cmd = f'.\sendmidi dev {self.dev_name} raw hex {msg}'
        ic(cmd)
        os.system(cmd)

    def send_midi(self, msg = "pc 2"):
        cmd = f'.\sendmidi dev {self.dev_name} {msg}'
        ic(cmd)
        os.system(cmd)

def handle_rx(_: int, data: bytearray):
    print("received:", data)

async def main(ble_address, UUID):
    # from stackoverflow
    # https://stackoverflow.com/questions/70116055/bleak-client-problem-with-sending-bytes-to-ble-device-e104-bt02
    device = await BleakScanner.find_device_by_address(ble_address, timeout=60.0)
    if not device:
        raise BleakError(f"A device with address {ble_address} could not be found.")
    async with BleakClient(ble_address) as client:
        await client.start_notify(UUID, handle_rx)
        print("Connected...")
        loop = asyncio.get_running_loop()
        while True:
            for i in range(0,7):
            #data = await loop.run_in_executor(None, sys.stdin.buffer.readline)
                data = "80 80 c0 " +  hex(i)[2:].zfill(2)
                if data == b'\r\n':
                    break
                data_hex = bytearray.fromhex(str(data.strip()).replace("b","").replace("'",""))
                await client.write_gatt_char(UUID, data_hex)
                ic(f"sent: {data} {data_hex}")
                await asyncio.sleep(3)

if __name__ == "__main__":
    m = MightyPlugPro()


    import time
    m.send_midi()
    time.sleep(5)
    m.send_midi_hex()
    time.sleep(5)

    asyncio.run(main(m.ble_address, m.UUID))

    # for mighty plu pro: 80 80 c0 01
    # program change to ch 1
    # for mighty plu pro: 80 80 c0 02
    # program change to ch 2
    # etc

    print('end')