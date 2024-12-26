import socket, glob, json
from database.db import query_cache, insert_into_cache
from logg.dns_logging_config import logging

port = 53
ip = '127.0.0.1'

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind((ip, port))

def load_zones():
    """Load zone files into memory."""
    jsonzone = {}
    zonefiles = glob.glob('zones/*.zone')

    for zone in zonefiles:
        with open(zone) as zonedata:
            data = json.load(zonedata)
            zonename = data["$origin"]
            jsonzone[zonename] = data
    return jsonzone

zonedata = load_zones()

def getflags(flags):
    """Process the flags from the DNS query."""
    byte1 = bytes(flags[:1])
    byte2 = bytes(flags[1:2])

    rflags = ''
    QR = '1'
    OPCODE = ''
    for bit in range(1,5):
        OPCODE += str(ord(byte1)&(1<<bit))

    AA = '1'
    TC = '0'
    RD = '0'

    RA = '0'
    Z = '000'
    RCODE = '0000'

    return int(QR+OPCODE+AA+TC+RD, 2).to_bytes(1, byteorder='big') + int(RA+Z+RCODE, 2).to_bytes(1, byteorder='big')

def getquestiondomain(data):
    """Extract the domain and question type from the DNS query."""
    state = 0
    expectedlength = 0
    domainstring = ''
    domainparts = []
    x = 0
    y = 0
    for byte in data:
        if state == 1:
            if byte != 0:
                domainstring += chr(byte)
            x += 1
            if x == expectedlength:
                domainparts.append(domainstring)
                domainstring = ''
                state = 0
                x = 0
            if byte == 0:
                domainparts.append(domainstring)
                break
        else:
            state = 1
            expectedlength = byte
        y += 1

    questiontype = data[y:y+2]
    return (domainparts, questiontype)

def getzone(domain):
    """Check if the domain is in a zone file."""
    global zonedata
    zone_name = '.'.join(domain)
    for zone in zonedata:
        if zone_name.endswith(zone):
            return zonedata[zone]
    return None

def getrecs(data):
    """Retrieve DNS records from cache or zone file."""
    domain, questiontype = getquestiondomain(data)
    qt = ''
    
    if questiontype == b'\x00\x01':  # A record
        qt = 'a'
    elif questiontype == b'\x00\x1c':  # AAAA record
        qt = 'aaaa'
    elif questiontype == b'\x00\x06':  # SOA record
        qt = 'soa'

    # Check cache first
    cached_record = query_cache('.'.join(domain))
    if cached_record:
        logging.info(f"Cache hit for domain: {'.'.join(domain)}")
        return [{"name": domain, "ttl": 3600, "value": cached_record}], qt, domain

    # If not in cache, fetch from zone
    zone = getzone(domain)
    if zone:
        records = []
        if qt in zone:
            for record in zone[qt]:
                if record['name'] == '@' or record['name'] == '.'.join(domain):
                    records.append(record)
                    # Cache the record for future use
                    insert_into_cache('.'.join(domain), record["value"])
        return records, qt, domain
    return [], qt, domain

def buildquestion(domainname, rectype):
    """Build the DNS question portion of the response."""
    qbytes = b''
    for part in domainname:
        length = len(part)
        qbytes += bytes([length])
        for char in part:
            qbytes += ord(char).to_bytes(1, byteorder='big')

    if rectype == 'a':
        qbytes += (1).to_bytes(2, byteorder='big')

    qbytes += (1).to_bytes(2, byteorder='big')

    return qbytes

def rectobytes(domainname, rectype, recttl, recval):
    """Convert DNS records into byte format."""
    rbytes = b'\xc0\x0c'

    if rectype == 'a':
        rbytes = rbytes + bytes([0]) + bytes([1])

    rbytes = rbytes + bytes([0]) + bytes([1])
    rbytes += int(recttl).to_bytes(4, byteorder='big')

    if rectype == 'a':
        rbytes = rbytes + bytes([0]) + bytes([4])
        for part in recval.split('.'):
            rbytes += bytes([int(part)])

    return rbytes

def buildresponse(data):
    """Build the full DNS response."""
    TransactionID = data[:2]
    Flags = getflags(data[2:4])
    QDCOUNT = b'\x00\x01'

    records, rectype, domainname = getrecs(data[12:])
    ANCOUNT = len(records).to_bytes(2, byteorder='big')
    NSCOUNT = (0).to_bytes(2, byteorder='big')
    ARCOUNT = (0).to_bytes(2, byteorder='big')

    dnsheader = TransactionID + Flags + QDCOUNT + ANCOUNT + NSCOUNT + ARCOUNT

    dnsbody = b''
    dnsquestion = buildquestion(domainname, rectype)

    for record in records:
        dnsbody += rectobytes(domainname, rectype, record["ttl"], record["value"])

    return dnsheader + dnsquestion + dnsbody


while True:
    data, addr = sock.recvfrom(512)
    r = buildresponse(data)
    sock.sendto(r, addr)
