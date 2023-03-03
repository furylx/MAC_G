#!/usr/bin/env python
import json
import subprocess
import optparse
import re
import os.path

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


def get_args():
    pass


def file_check():
    os.path.exists('./oldmac.json')


def get_interfaces():
    out = subprocess.check_output(['ifconfig', '-s'])
    out_list = {i + 1: line.split()[0] for i, line in enumerate(out.decode().split('\n')[1:-1])}
    return out_list


def get_mac(interface):
    out = subprocess.check_output(['ifconfig', interface])
    if out:
        out_list = [line.strip() for line in out.decode().split('\n')[1:] if line.strip()[:5] == 'ether']
        ether = ''.join(out_list)
        try:
            mac_address = (
                re.search(r'([0-9A-Fa-f]{2}[:]){5}[0-9A-Fa-f]{2}|([0-9A-Fa-f]{2}[-]){5}[0-9A-Fa-f]{2}', ether)).group(0)
            if mac_address:
                return mac_address
        except:
            print(f"Could not find a mac address on \'{interface}\'")


def valid_mac(mac):
    mac_address = (
        re.search(r'([0-9A-Fa-f]{2}[:]){5}[0-9A-Fa-f]{2}|([0-9A-Fa-f]{2}[-]){5}[0-9A-Fa-f]{2}', mac))  # .group(0)
    if mac_address is None:
        return False
    else:
        return True


def change_mac(interface, mac):
    if not valid_mac(mac):
        print(f"{mac} is not a valid mac address!")
    elif get_mac(interface) == mac.replace('-', ':'):
        print(f"{interface} already has the mac {mac}")
    else:
        mac = mac.replace('-', ':')
        with open('oldmac.json', 'w') as f:
            json.dump(get_mac(interface), f, indent=4)
        print(f"Changing mac address on {interface} to {mac}")
        subprocess.call(['ifconfig', interface, 'down'])
        subprocess.call(['ifconfig', interface, 'hw', 'ether', mac])
        subprocess.call(['ifconfig', interface, 'up'])


def reset_mac(interface):
    if file_check():
        with open('oldmac.json', 'r') as f:
            old_mac = json.load(f)
        print(f"Reverting mac address on {interface} back to {old_mac}")
        subprocess.call(['ifconfig', interface, 'down'])
        subprocess.call(['ifconfig', interface, 'hw', 'ether', old_mac])
        subprocess.call(['ifconfig', interface, 'up'])
    else:
        print(
            f"\nCould not revert to previous mac because the mac probably has not been changed.\nIf you change your mac, the old mac will be backed up.")


def main():
    print(art)
    interface_dict = ", ".join([f"{key}: {value}" for key, value in get_interfaces().items()])
    interface_choice = ", ".join([f"{key}" for key in get_interfaces().keys()])
    print(f"\nAvailable interfaces: {interface_dict}")
    user_interface_choice = int(input(f"\nChoose the interface {interface_choice}:\n\n"))
    if str(user_interface_choice) not in str(interface_choice):
        print(f"{user_interface_choice} was not a valid choice, ciao!")
        return
    if get_mac(get_interfaces()[user_interface_choice]) is not None:
        print(
            f"\nMac address of {get_interfaces()[user_interface_choice]} is {get_mac(get_interfaces()[user_interface_choice])}")
        change_or_revert = input(
            "Enter \'revert\' to revert back to your previous mac address, \'change\' to change it or \'exit\' to stop.\n\n")
        if change_or_revert.lower() == 'change':
            new_mac = input("Enter the new mac address you want to use\n\n")
            change_mac(get_interfaces()[user_interface_choice], new_mac)
        elif change_or_revert.lower() == 'revert':
            reset_mac(get_interfaces()[user_interface_choice])
        elif change_or_revert.lower() == 'exit':
            print("\nBye!")
        else:
            print('You did not enter a valid command!')


if __name__ == '__main__':
    main()
