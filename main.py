from argparse import ArgumentParser
import subprocess
import json
import re
import random

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

# TODO WITH THE IP COMMAND MAC MUST HAVE :, - IS NOT VALID!
out_json = subprocess.check_output(['ip', '-j', 'a'])
out = json.loads(out_json.decode())


def get_interfaces():
    return [dic['ifname'] for dic in out if 'address' in dic.keys()]


def get_mac(interface):
    mac = [dic['address'] for dic in out if interface in dic.values()]
    return ''.join(mac)


def change_mac(interface, mac):
    try:
        subprocess.call(['ip', 'link', 'set', 'dev', interface, 'down'])
        subprocess.call(['ip', 'link', 'set', 'dev', interface, 'address', mac])
        subprocess.call(['ip', 'link', 'set', 'dev', interface, 'up'])
        print(f"MAC address has been changed to {mac}")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")


def valid_mac(mac):
    print(f"Mac inside valid mac >{mac}<")
    mac_address = (re.search(r'([0-9A-Fa-f]{2}[:]){5}[0-9A-Fa-f]{2}', mac))# check if the mac has a valid format (not checking UAA,LAA and multi- or unicast)
    if mac_address is None:
        return False
    else:
        return True


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


def mac_generator_vendor(vendor_octets):
    if len(vendor_octets) == 8 and re.search(r'([0-9A-Fa-f]{2}[:]){2}[0-9A-Fa-f]{2}', vendor_octets) is not None:
        mac_address = []

        for i in range(3):
            mac_address.append(random.randint(0x00, 0xff))
        mac_str = ':'.join('{:02x}'.format(byte) for byte in mac_address)

        return vendor_octets + ':' + mac_str
    else:
        print("The format must be \'xx:xx:xx\', the last 3 octets are generated automatically.")


def main():
    print(art)
    parser = ArgumentParser()
    # Optional positional argument for interface
    parser.add_argument('interface', nargs='?', help='Specify interface')

    # Options for setting MAC address
    parser.add_argument('-U', action='store_true', help='Set random UAA MAC address')
    parser.add_argument('-L', action='store_true', help='Set random LAA MAC address')
    parser.add_argument('-v', metavar='XX:XX:XX', help='Set MAC address using vendor prefix')
    parser.add_argument('-c', metavar='XX:XX:XX:XX:XX:XX', help='Set MAC address to specified value')

    # Option for showing available interfaces
    parser.add_argument('--show', action='store_true', help='Show available interfaces with MAC addresses')

    args = parser.parse_args()

    if args.show:
        print(get_interfaces())
        print("Because show...")

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
