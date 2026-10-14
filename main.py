import asyncio
from functools import partial
from bleak import BleakScanner, BleakClient

ADDITIONAL_STATUS = "ce060032-43e5-11e4-916c-0800200c9a66"
GENERAL_STATUS = "ce060031-43e5-11e4-916c-0800200c9a66"   # has distance
ERG_TABLE = {}   # erg name -> rower name
DISTANCES = {}   # rower name -> meters rowed
SPLIT = {}       # rower name -> split in seconds
RATE = {}        # rower name -> rate



async def find_all_pm5s():
    devices = await BleakScanner.discover(timeout=10)
    pm5s = []

    for device in devices:
        if device.name and device.name.startswith("PM5"):
            pm5s.append(device)

    print("Found", len(pm5s), "PM5s")
    return pm5s


def on_data(name, sender, data):
    stroke_rate = data[5]
    split_in_seconds = (data[7] + data[8] * 256) / 100      # seconds per 500 m

    rower = ERG_TABLE[name]
    SPLIT[rower] = split_in_seconds
    RATE[rower] = stroke_rate

    #print(name, "  Split:", split, "sec   Rate:", stroke_rate, "spm")


def on_distance(name, sender, data):
    distance = (data[3] + data[4] * 256 + data[5] * 65536) / 10   # meters
    rower = ERG_TABLE[name]
    DISTANCES[rower] = distance


async def connect_all(pm5s):
    clients = []

    for device in pm5s:                          # one at a time, connecting all at once tends to fail
        client = BleakClient(device)

        try:
            await client.connect() #bt connect
            await client.start_notify(ADDITIONAL_STATUS, partial(on_data, device.name)) # getting rate and Split
            await client.start_notify(GENERAL_STATUS, partial(on_distance, device.name)) # getting distance
            clients.append(client)
            print("Connected to", device.name)
        except Exception as error:
            print("Could not connect to", device.name, "-", error)
    return clients


def assign_rower(pm5s):
    for device in pm5s:
        print(device.name)
        rower = input("Who is it that occupieth the ergometer?")
        ERG_TABLE[device.name] = rower


def format_split(split):
    if split == 0:
        return "-:--.-"
    minutes = int(split // 60)
    seconds = split % 60
    return f"{minutes}:{seconds:04.1f}"



async def main():
    pm5s = await find_all_pm5s()
    assign_rower(pm5s)
    clients = await connect_all(pm5s)

    while True:
        await asyncio.sleep(1)




    for client in clients:
        await client.disconnect()


asyncio.run(main())
