import sys
import os
import asyncio
import binascii
from icecream import ic
from bleak import BleakScanner, BleakError, BleakClient

import ble_midi_timestamp

class HexFmt:
    def __init__(self, hex_string:str):
        hex_string = str(hex_string.strip())
        hex_string = hex_string.replace("'","").replace(":","").replace("\\r","").replace("\\n","")
        hex_string = hex_string.strip()
        self.hex_string = hex_string
        self.hex_bytes = ':'.join('{:02x}'.format(byte) for byte in bytes.fromhex(self.hex_string))
        self.hex_bytes_spaced = ' '.join('{:02x}'.format(byte) for byte in bytes.fromhex(self.hex_string))
        self.byte_array = bytearray.fromhex(hex_string)

    def __str__(self):
        # for easy printing
        return str(self.hex_bytes)

class KatanaGo:
    # description of BLE timestamps:
    # https://hangar42.nl/wp-content/uploads/2017/10/BLE-MIDI-spec.pdf
    # BLE_MIDI_HEADER
    # BLE_MIDI_TS TimeStampLow

    def __init__(self):
        self.dev_name = "KATANA:GO"
        # self.dev_name = "KTN-GO"
        self.BLE_MIDI_HEADER = "94"
        self.BLE_MIDI_TS = "F4"
        self.STX = "F0"
        self.ROLAND = "41"
        self.DEV_ID = "10"
        self.MODEL_ID = "01050D"
        # 12 = DT1 (data set), 11= RQ1 (request)
        self.RQ1 = '11'
        self.DT1 = '12'
        self.EOX = "F7"
        self.DATA = "7F0001000000"
        self.CHECKSUM = "00"

        self.ble_address = "CB:4E:FD:B8:FD:F5"
        BLE_MODEL_NBR_UUID_MIDI_SERVICE = "03B80E5A-EDE8-4B33-A751-6CE34EC4C700"
        BLE_MODEL_NBR_UUID_MIDI_DATA_IO = "7772E5DB-3868-4112-A1A9-F2669D106BF3"
        self.UUID = BLE_MODEL_NBR_UUID_MIDI_DATA_IO

        # captured with android app and BLE sniffer & wireshark
        # todo minimize this list
        self.ble_start_list = []
        self.ble_start_list.append('9c:8c:f0:7e:10:06:01:8c:f7')
        self.ble_start_list.append('8b:cf:f0:7e:10:06:02:41:0d:05:00:00:00:00:00:00:cf:f7')

        self.ble_start_list.append('b9:8f:f0:7e:10:06:01:8f:f7')
        self.ble_start_list.append('a8:d4:f0:7e:10:06:02:41:0d:05:00:00:00:00:00:00:d4:f7')

        self.ble_start_list.append('96:9a:f0:7e:10:06:01:9a:f7')
        self.ble_start_list.append('96:9a:f0:7e:10:06:01:9a:f7')
        self.ble_start_list.append('85:d5:f0:7e:10:06:02:41:0d:05:00:00:00:00:00:00:d5:f7')

        self.ble_start_list.append('b3:a0:f0:7e:10:06:01:a0:f7')
        self.ble_start_list.append('a2:d9:f0:7e:10:06:02:41:0d:05:00:00:00:00:00:00:d9:f7')

        self.ble_start_list.append('90:a4:f0:7e:10:06:01:a4:f7')
        self.ble_start_list.append('bf:e1:f0:7e:10:06:02:41:0d:05:00:00:00:00:00:00:e1:f7')

        self.ble_start_list.append('ad:9d:f0:7e:10:06:01:9d:f7')
        self.ble_start_list.append('9c:c5:f0:7e:10:06:02:41:0d:05:00:00:00:00:00:00:c5:f7')

#        self.ble_start_list.append('01:00')
#        self.ble_start_list.append('01:18')
#        self.ble_start_list.append('00:00')
        self.ble_start_list.append('a9:ec:f0:7e:00:06:01:ec:f7')

        self.ble_start_list.append('88:a8:f0:7e:10:06:02:41:0d:05:00:00:00:00:00:00:a8:f7')
        self.ble_start_list.append('96:b4:f0:41:10:01:05:0d:11:7f:00:00:00:00:00:00:01:00:b4:f7')
        self.ble_start_list.append('88:ed:f0:41:10:01:05:0d:12:7f:00:00:00:00:01:ed:f7')
        self.ble_start_list.append('96:f0:f0:41:10:01:05:0d:12:7f:00:00:01:01:7f:f0:f7')
        self.ble_start_list.append('96:fa:f0:41:10:01:05:0d:11:7f:01:00:04:00:00:00:01:7b:fa:f7')
        self.ble_start_list.append('89:b1:f0:41:10:01:05:0d:12:7f:01:00:04:00:7c:b1:f7')
        self.ble_start_list.append('97:d2:f0:41:10:01:05:0d:11:7f:00:00:03:00:00:00:01:7d:d2:f7')

        # load default class container values
        self.compose_sys_ex_msg()

    def cksum(self, hex_string = "2000700000000001"):
        '''
        MIDI SYS_EX checksum calculation
        7f:00:01:00:00:04 returns checksum 7c
        '''
        # Take the data with last two bytes where f7 is the last 
        hex_string = hex_string.lower()
        vals = bytearray.fromhex(hex_string.replace(":", ""))
        # Sum with 7-bit wraparound
        accum = 0
        for val in vals:
            accum = (accum + val) & 0x7F
        # Checksum is lower 7 bits of the difference w/ 128
        cksum = (128 - accum) & 0x7F
        self.CHECKSUM = format(cksum, '02X')
        return self.CHECKSUM

    def compose_sys_ex_msg(self, DATA = "7f0001000000"):
        '''
        compose midi and ble_midi sys_ex messages
        add required timestamps for ble_midi
        results are stored in class container
        the midi message is return as string

        single line only implemented
        '''
        self.DATA = DATA.lower()
        self.cksum(self.DATA)
        # single packet / line sys_ex command for ble_midi
        self.msg_ble_midi_sys_ex = f"{self.BLE_MIDI_HEADER}{self.BLE_MIDI_TS}"
        self.msg_ble_midi_sys_ex += f"{self.STX}{self.ROLAND}{self.DEV_ID}{self.MODEL_ID}{self.DT1}"
        self.msg_ble_midi_sys_ex += f"{self.DATA}{self.CHECKSUM}{self.BLE_MIDI_TS}{self.EOX}"
        self.msg_ble_midi_sys_ex = HexFmt(self.msg_ble_midi_sys_ex)

        # single line sys_ex command for wired midi
        self.msg_midi_sys_ex = f"{self.STX}{self.ROLAND}{self.DEV_ID}{self.MODEL_ID}{self.DT1}"
        self.msg_midi_sys_ex += f"{self.DATA}{self.CHECKSUM}{self.EOX}"
        self.msg_midi_sys_ex = HexFmt(self.msg_midi_sys_ex)
        return 
    
    def midi_dbg(self):
        # from katana go playstoor app apk midi_dbg.js
        head = f"{self.STX}{self.ROLAND}{self.DEV_ID}{self.MODEL_ID}"
        headLen = len(head)
        msg = self.msg_midi_sys_ex.hex_string.upper()
        result = ""
        msg_filt = msg[(headLen + 0):(headLen + 2)]
        if msg_filt == '12':
            result += '[DT]'
        elif msg_filt == '11':
            result += '[RQ]'
        
        # js case statement:
        msg_filt = msg[(headLen + 2):(headLen + 4)]
        if msg_filt == '60':
            msg_filt = msg[(headLen + 4):(headLen + 10)]
            if msg_filt == '000720':
                result += '[CHAIN    ]'
            else:
                result += '[CMD][PRM]'
#                result = pramInfo(result, msg)

        elif msg_filt == '7F':
            result += '[CMD]'
            msg_filt = msg[(headLen + 4):(headLen + 10)]
            case = msg_filt
            if case == '000000':
                result += '[COM LEVEL]'
            elif case == '000001':
                result += '[COM MODE ]'
            elif case == '000002':
                result += '[RUN MODE ]'
            elif case == '000003':
                result += '[COM RIVIS]'
            elif case == '000100':
                result += '[PAT SELEC]'
            elif case == '000104':
                result += '[PAT WRITE]'
            elif case == '000106':
                result += '[PAT_INIT ]'
            elif case == '00010E':
                result += '[INIT     ]'
            elif case == '010003':
                result += '(PAT CLEAR)'
            elif case == '000300':
                result += '[TUN STATE ]'
            # Add more cases as needed
            else:
                result += '[UNKNOWN  ]'
        else:
            result += '[PRM]'
#            result = pramInfo(__, msg)

        self.midi_dbg_result = result
        ic(self.midi_dbg_result)
        return self.midi_dbg_result

    def send_midi_wired(self, data = ''):
        '''
        android apk shows wired midi is possible
        this could work via usbc cable and sendmidi,exe program
        as it does foe nux mighty plug pro
        https://github.com/gbevin/SendMIDI

        to send somethin data could be 7f 00 01 00 00 04
        the generated cmd could be:
        .\sendmidi.exe dev "KATANA:GO" raw hex 7f 00 01 00 00 04
        
        the sendmidi.exe should be in the same folder
        currently this does not work
        '''
        if data == '':
            send_string = HexFmt(self.msg_midi_sys_ex.hex_string).hex_bytes_spaced
        else:
            send_string = data
        cmd = f'sendmidi dev {self.dev_name} raw hex {send_string}'
        ic(cmd)
        os.system(cmd)
        return cmd

    def sys_ex_ble_midi_data(self, data):
        # process input
        data_in = HexFmt(data)

        # generate timestamp for ble_midi, store into class container
        ts = ble_midi_timestamp.ble_midi_timestamp()
        self.BLE_MIDI_HEADER = ts['BLE_MIDI_HEADER']
        self.BLE_MIDI_TS = ts['BLE_MIDI_TS']

        self.compose_sys_ex_msg(data_in.hex_string)

        result = {}
        result['data_in']= data_in.hex_bytes
        result['data_hex']= self.msg_ble_midi_sys_ex.hex_bytes
        result['data_bytearray']= self.msg_ble_midi_sys_ex.byte_array
        return result
    
    def program_change(self, pc=0, cmd='7f:00:01:00:00:xx'):
        '''
        patch select by number just as a normal midi "pc 0" command
        '''
        if int(pc) > 34:
            print('max pc value: 34')
        pc = format(int(pc), '02X')
        ic(pc)
        cmd = cmd.replace('xx',pc)
        ic(cmd)
        return cmd

    def amp_volume(self, pos=0, cmd='20:00:20:01:msb:lsb'):
        '''
        amp volume control
        under construction
        '''
        lsb = 0
        msb = int(pos)
        if int(pc) > 34:
            print('max  value: ?')
        lsb = format(int(lsb), '02X')
        msb = format(int(msb), '02X')
        ic(msb, lsb)
        cmd = cmd.replace('msb',msb).replace('lsb',lsb)
        ic(cmd)
        return cmd

    def wah_position(self, vol=0, cmd='20:02:50:01:msb:lsb'):
        '''
        amp volume control
        under construction
        '''
        lsb = 0
        msb = int(pos)
        if int(pos) > 34:
            print('max  value: ?')
        lsb = format(int(lsb), '02X')
        msb = format(int(msb), '02X')
        ic(msb, lsb)
        cmd = cmd.replace('msb',msb).replace('lsb',lsb)
        ic(cmd)
        return cmd

def handle_rx(_: int, data: bytearray):
    if data != None:
        data_in = binascii.hexlify(data).decode()
        formatted_hex_string = HexFmt(data_in)
    else:
        formatted_hex_string = ''
    print("received:", formatted_hex_string)

async def main(k: KatanaGo):
    # from stackoverflow
    # https://stackoverflow.com/questions/70116055/bleak-client-problem-with-sending-bytes-to-ble-device-e104-bt02
    device = await BleakScanner.find_device_by_address(k.ble_address, timeout=60.0)
    if not device:
        raise BleakError(f"A device with address {k.ble_address} could not be found.")
    async with BleakClient(k.ble_address) as client:

        await client.start_notify(k.UUID, handle_rx)

        print("Connected...")
        loop = asyncio.get_running_loop()
        # startup, repeat logged stuff, maybe not required ...
        for i in k.ble_start_list:
            # input validation
            ble_midi_hex_str = HexFmt(i)

            # get actual timestamp
            ts = ble_midi_timestamp.ble_midi_timestamp()
            BLE_MIDI_HEADER = ts['BLE_MIDI_HEADER']
            BLE_MIDI_TS = ts['BLE_MIDI_TS']

            # replace logged timestamps with actual
            ble_midi_hex_str = HexFmt(BLE_MIDI_HEADER + BLE_MIDI_TS + ble_midi_hex_str.hex_string[4:-4] + BLE_MIDI_TS + ble_midi_hex_str.hex_string[-2:])

            # write to device
            await client.write_gatt_char(k.UUID, ble_midi_hex_str.byte_array)

            # show debug info
            ic('write: ', ble_midi_hex_str.hex_bytes)

            # show katana apk debug stuff
            k.midi_dbg()
            
            # wait for the device to catch up
            await asyncio.sleep(.1)
        
        print("Enter decimal program change number , or only  <ENTER> to exit.")
        while True:

            # start input prompt
            data = await loop.run_in_executor(None, sys.stdin.buffer.readline)
            if data == b'\r\n':
                break

            # input validation
            data_tmp = str(data.strip().decode('utf-8')).lower()
            data_tmp = data_tmp.replace("'","").replace(":","").replace("\\r","").replace("\\n","")

            cmd = k.program_change(data_tmp)

            # process user input
            #sys_ex_ble_midi_data = k.sys_ex_ble_midi_data(cmd)
            k.sys_ex_ble_midi_data(cmd)

            # write ble_midi data
            await client.write_gatt_char(k.UUID, k.msg_ble_midi_sys_ex.byte_array, response=False)

            # show debug info
            ic('write: ', k.msg_ble_midi_sys_ex.hex_bytes)

            # show katana apk debug stuff
            k.midi_dbg()
            
            # wait for the device to catch up
            await asyncio.sleep(.1)

if __name__ == "__main__":
    # Example usage:
    k = KatanaGo()
    asyncio.run(main(k))

    #k.send_midi_wired()

    print('end')