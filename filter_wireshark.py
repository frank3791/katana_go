import json

# first save file to json file in wireshark program

# Open the JSON file
file_info = '20apr2024.json'
file_info = 'scan_mightypro_27apr2024.txt.pcapng.json'
file_info = '20240503_katana_amp_vol_and_next_wah.json'

with open(file_info) as file:
    data = json.load(file)

def filter_json_by_key(data, target_key, frame_nr=0):
    filtered_data = []
    if isinstance(data, dict):
        if "frame" in data:
            frame = data
            frame_nr = frame['frame']
        if target_key in data:
            data['frame.number'] = frame_nr['frame.number']
            filtered_data.append(data)
        for value in data.values():
            filtered_data.extend(filter_json_by_key(value, target_key, frame_nr))
    elif isinstance(data, list):
        for item in data:
            filtered_data.extend(filter_json_by_key(item, target_key, frame_nr))

    return filtered_data

def find_value_by_key(data, target_key):
    if isinstance(data, dict):
        for key, value in data.items():
            if key == target_key:
                return value
            else:
                result = find_value_by_key(value, target_key)
                if result is not None:
                    return result
    elif isinstance(data, list):
        for item in data:
            result = find_value_by_key(item, target_key)
            if result is not None:
                return result
    return None

def collect_values_and_frame(filtered_data):
    filtered_values = []
    for i in filtered_data:
        item = {}
        item['value'] = find_value_by_key(i, 'btatt.value')
        item['frame_nr'] = find_value_by_key(i, 'frame.number')
        filtered_values.append(item)
    return filtered_values

if __name__ == "__main__":
    filtered_data = filter_json_by_key(data, 'btatt.value')
    filtered_values = collect_values_and_frame(filtered_data)
    # Write the array of dictionaries to a MD file
    filename_new = file_info.replace('.json', '_filtered.md')
    with open(filename_new, 'w') as file:
        file.write(f"# Filtered Values: {filename_new}\n\n")
        frame_old=1e12
        for item in filtered_values:
            # asume new command when frames step > 100
            frame_new = int(item['frame_nr'])
            if frame_new > frame_old+100:
                file.write("\n")
            file.write(f"frame_nr: {frame_new} value: {item['value']}\n")
            frame_old = frame_new

    print('end')