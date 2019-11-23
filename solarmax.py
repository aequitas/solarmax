import os
import socket
import sys
import time

IDC = "IDC"   # DC Current
UL1 = "UL1"   # Voltage Phase 1
TKK = "TKK"   # inverter operating temp
IL1 = "IL1"   # current phase 1
SYS = "SYS"   # 4E28 = 17128
TNF = "TNF"   # generated frequency (Hz)
UDC = "UDC"   # DC voltage (V DC)
PAC = "PAC"   # AC power being generated * 2 (W)
PRL = "PRL"   # relative output (%)
KT0 = "KT0"   # total yield (kWh)

field_map = {
    IDC: 'dc_current',
    UL1: 'voltage_phase1',
    TKK: 'inverter_temp',
    IL1: 'current_phase1',
    SYS: 'sys',
    TNF: 'frequency',
    UDC: 'dc_voltage',
    PAC: 'power_output',
    PRL: 'relative_ouput',
    KT0: 'total_yield'
}


req_data = b'{FB;01;3E|64:IDC;UL1;TKK;IL1;SYS;TNF;UDC;PAC;PRL;KT0;SYS|0F66}'

def genData(s):
    """ takes a pair: <field>=<0xdata> and converts to a list
    with the name mapped using field_map and value converted to base 10 and appropriately scaled """

    t = s.split('=')
    f = t[0]

    if (f == SYS):   # remove the trailing ,0
        v = int(t[1][:t[1].find(',')], 16)
    else:
        v = int(t[1], 16)

    if (f == PAC):    # PAC values are *2 for some reason
        v = v/2

    if (f == UL1 or f == UDC):  # voltage levels need to be divide by 10
        v = v/10.0

    if (f == IDC or f == TNF):  # current & frequency needs to be divided by 100
        v = v/100.0

    return [field_map[f], v]

def convert_data(data):
    """Convert the inverter message to JSON
    >>> convert_data('{01;FB;70|64:IDC=407;UL1=A01;TKK=2C;IL1=46D;SYS=4E28,0' \
    ';TNF=1383;UDC=B7D;PAC=16A6;PRL=2B;KT0=48C;SYS=4E28,0|1A5F}') == \
    {'relative_ouput': 43, 'total_yield': 1164, 'power_output': 2899.0, 'dc_current': 10.31, 'inverter_temp': 44, \
    'voltage_phase1': 256.1, 'current_phase1': 1133, 'sys': 20008, 'frequency': 49.95, 'dc_voltage': 294.1}
    True
    """
    # pull out the data elements into a list  and replace the code with the json field name
    ev = [genData(s) for s in data[data.find(':')+1:data.find('|', data.find(':'))].split(';')]

    return (dict(ev))

def connect_to_inverter(inverter_ip, inverter_port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(10)
        s.connect((inverter_ip, inverter_port))
    except socket.error as msg:
        print('Failed to create socket: Error code: ' + str(msg))
        sys.exit()
    return s

def read_data(sock, request):
    sock.send(request)
    data_received = False
    response = b''
    while not data_received:
        buf = sock.recv(1024)
        if len(buf) > 0:
            response = response + buf
            data_received = True
    return response.decode('utf8')

def print_graphite(data, graphite_prefix, now):
    """Output metrics in graphite carbon compatible format.
    >>> print_graphite({'test':123}, 'prefix.', 123456789)
    prefix.solarmax.test 123 123456789

    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for metric, value in data.items():
        msg = '{prefix}solarmax.{metric} {value} {time}'.format(
            prefix=graphite_prefix,
            metric=metric,
            value=value,
            time=now,
        )
        print(msg)
        sock.sendto(msg + '\n', ('127.0.0.1', 2003))

def main():
    inverter_ip = os.environ.get('INVERTER_IP', '192.168.2.123')
    inverter_port = int(os.environ.get('INVERTER_PORT', 12345))
    graphite_prefix = os.environ.get('GRAPHITE_PREFIX', '')

    while True:
        # get current epoch timestamp
        now = int(time.time())

        inv_s = connect_to_inverter(inverter_ip, inverter_port)
        try:
            data = read_data(inv_s, req_data)
            data = convert_data(data)
            print_graphite(data, graphite_prefix, now)
        finally:
            inv_s.shutdown(socket.SHUT_RD)
            inv_s.close()

        time.sleep(10)

if __name__ == "__main__":
    main()
