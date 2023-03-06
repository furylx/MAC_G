from argparse import ArgumentParser
import subprocess
import json
import re
import random
import requests
import os
import sqlite3

art = '''

          _____                    _____                    _____                                    _____          
         /\    \                  /\    \                  /\    \                                  /\    \         
        /::\____\                /::\    \                /::\    \                                /::\    \        
       /::::|   |               /::::\    \              /::::\    \                              /::::\    \       
      /:::::|   |              /::::::\    \            /::::::\    \                            /::::::\    \      
     /::::::|   |             /:::/\:::\    \          /:::/\:::\    \                          /:::/\:::\    \     
    /:::/|::|   |            /:::/__\:::\    \        /:::/  \:::\    \                        /:::/  \:::\    \    
   /:::/ |::|   |           /::::\   \:::\    \      /:::/    \:::\    \                      /:::/    \:::\    \   
  /:::/  |::|___|______    /::::::\   \:::\    \    /:::/    / \:::\    \                    /:::/    / \:::\    \  
 /:::/   |::::::::\    \  /:::/\:::\   \:::\    \  /:::/    /   \:::\    \                  /:::/    /   \:::\ ___\ 
/:::/    |:::::::::\____\/:::/  \:::\   \:::\____\/:::/____/     \:::\____\                /:::/____/  ___\:::|    |
\::/    / ~~~~~/:::/    /\::/    \:::\  /:::/    /\:::\    \      \::/    /                \:::\    \ /\  /:::|____|
 \/____/      /:::/    /  \/____/ \:::\/:::/    /  \:::\    \      \/____/                  \:::\    /::\ \::/    / 
             /:::/    /            \::::::/    /    \:::\    \                               \:::\   \:::\ \/____/  
            /:::/    /              \::::/    /      \:::\    \                               \:::\   \:::\____\    
           /:::/    /               /:::/    /        \:::\    \                               \:::\  /:::/    /    
          /:::/    /               /:::/    /          \:::\    \                               \:::\/:::/    /     
         /:::/    /               /:::/    /            \:::\    \                               \::::::/    /      
        /:::/    /               /:::/    /              \:::\____\                               \::::/    /       
        \::/    /                \::/    /                \::/    /                                \::/____/        
         \/____/                  \/____/                  \/____/                                                  


'''

DB_FILE = 'oui.db'
out_json = subprocess.check_output(['ip', '-j', 'a'])
out = json.loads(out_json.decode())

# Getting all the interfaces that have a mac
def get_interfaces():
    return [dic['ifname'] for dic in out if 'address' in dic.keys()]

# Get the mac from the chosen interface
def get_mac(interface):
    mac = [dic['address'] for dic in out if interface in dic.values()]
    return ''.join(mac)

# main function to change the mac
def change_mac(interface, mac):
    try:
        subprocess.call(['ip', 'link', 'set', 'dev', interface, 'down'])
        subprocess.call(['ip', 'link', 'set', 'dev', interface, 'address', mac])
        subprocess.call(['ip', 'link', 'set', 'dev', interface, 'up'])
        print(f"MAC address has been changed to {mac}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

# mac validation, only format not UAA,LAA and not multi- or unicast
def valid_mac(mac):
    print(f"Mac inside valid mac >{mac}<")
    mac_address = (re.search(r'([0-9A-Fa-f]{2}[:]){5}[0-9A-Fa-f]{2}', mac))
    if mac_address is None:
        return False
    else:
        return True

# Mac generator, yes useless cases, but I wrote the function before I knew important stuff about uni- and multicast
def mac_generator(user_uaa=False, user_multicast=False):
    '''I hope this is alright xD As far as I understand it is and works.'''

    first_byte = random.randint(0x00, 0xff)

    # Set the administration type (UAA or LAA) bit (second least significant bit)
    if user_uaa:
        first_byte = first_byte & ~(1 << 1)  # set the bit to 0 // first_byte AND NOT(1 LSHIFT 1)
    else:
        first_byte = first_byte | (1 << 1)  # set the bit to 1 // first_byte  OR (1 LSHIFT 1)

    # Set the transmission type (uni- or multicast) bit (least significant bit)
    if user_multicast:
        first_byte = first_byte | 1  # set the bit to 1 // first_byte OR 1
    else:
        first_byte = first_byte & ~1  # set the bit to 0 // first_byte AND NOT 1

    mac_address = [first_byte]

    for i in range(5):
        mac_address.append(random.randint(0x00, 0xff))

    mac_str = ':'.join('{:02x}'.format(byte) for byte in mac_address)
    return mac_str

# Takes the OUI from the user and appends 3 random octets
def mac_generator_vendor(vendor_octets):
    if len(vendor_octets) == 8 and re.search(r'([0-9A-Fa-f]{2}[:]){2}[0-9A-Fa-f]{2}', vendor_octets) is not None:
        mac_address = []

        for i in range(3):
            mac_address.append(random.randint(0x00, 0xff))
        mac_str = ':'.join('{:02x}'.format(byte) for byte in mac_address)

        return vendor_octets + ':' + mac_str
    else:
        print("The format must be \'xx:xx:xx\', the last 3 octets are generated automatically.")

# creating the db off of the OUI.txt from IEEE
def update_db():
    conn = sqlite3.connect('oui.db')
    c = conn.cursor()

    # Check if oui table exists
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='oui'")
    table_exists = c.fetchone() is not None

    if not table_exists:
        # Create table for MAC address prefixes and company names
        c.execute('''CREATE TABLE oui
                     (prefix TEXT PRIMARY KEY, company TEXT)''')

    # Download the OUI text file
    response = requests.get('https://standards-oui.ieee.org/oui/oui.txt')
    response.raise_for_status()

    # Extract the company name and MAC address prefix
    pattern = re.compile(r'^([0-9A-Fa-f]{2}-[0-9A-Fa-f]{2}-[0-9A-Fa-f]{2})\s+\(hex\)\s+(.+)$', re.MULTILINE)
    matches = pattern.findall(response.text)

    # Insert or update each MAC address prefix and company name in the database
    for mac, name in matches:
        c.execute("INSERT OR REPLACE INTO oui (prefix, company) VALUES (?, ?)", (mac, name))

    # Commit changes and close connection
    conn.commit()
    conn.close()

# Fetching the vendor from the db
def get_vendor(prefix):
    # Connect to db
    prefix = prefix.upper()
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Search db for vendor based on prefix
    c.execute("SELECT company FROM oui WHERE prefix=?", (prefix,))
    result = c.fetchone()

    conn.close()
    return result[0] if result else None

# deleting the db because updating it seems impossible for me at this time. Update workflow -> delete, create new
def clear_db():
    # Remove the database file if it exists
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)


def main():
    print(art)
    parser = ArgumentParser()
    # Positional argument for interface
    parser.add_argument('interface', nargs='?', help='Specify interface')

    # Options for setting MAC address
    parser.add_argument('-U', action='store_true', help='Set random UAA MAC address')
    parser.add_argument('-L', action='store_true', help='Set random LAA MAC address')
    parser.add_argument('-v', metavar='XX:XX:XX', help='Set MAC address using vendor prefix')
    parser.add_argument('-c', metavar='XX:XX:XX:XX:XX:XX', help='Set MAC address to specified value')

    # Database related things
    parser.add_argument('--vendor', metavar='XX:XX:XX', help='Looks up the prefix at ieee')
    parser.add_argument('--update', action='store_true', help='Updates the OUI database or downloads it if not existing')
    parser.add_argument('--clear', action='store_true', help='Deletes the OUI database')

    # Option for showing available interfaces
    parser.add_argument('--show', action='store_true', help='Show available interfaces with MAC addresses')

    args = parser.parse_args()

    if args.show:
        print(get_interfaces())

    elif args.vendor:
        vendor = get_vendor(args.vendor)
        if vendor is None:
            print("Prefix not found")
        else:
            print(vendor)

    elif args.update:
        print("\n IF NOTHING HAPPENS AFTER ABOUT 1 MINUTE, PRESS CTRL+C, RUN --clear AND TRY AGAIN. UNLESS YOU ARE SURE IT IS BECAUSE OF YOUR INTERNET\n")
        update_db()

    elif args.clear:
        clear_db()
    else:
        if not args.interface:
            print(
                "Interface argument is required when setting or changing the MAC address. Use -h to see the available options.")

        else:
            if args.v and not any([args.L, args.c, args.U]):
                if mac_generator_vendor(args.v) is None:
                    pass
                else:
                    change_mac(args.interface, mac_generator_vendor(args.v))

            elif args.c and not any([args.L, args.U, args.v]):
                if valid_mac(args.c):
                    change_mac(args.interface, valid_mac(args.c))
                else:
                    print(f"The mac address you entered is not valid")
            elif args.U and not any([args.L, args.c, args.v]):
                change_mac(args.interface, mac_generator(True, False))

            elif args.L and not any([args.U, args.c, args.v]):
                change_mac(args.interface, mac_generator())

            else:
                print("Invalid combination of arguments. Use -h to see the available options.")


if __name__ == '__main__':
    main()
