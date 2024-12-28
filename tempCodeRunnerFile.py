# dns_server.py

import socket
import glob
import json
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Union
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DNSQuestion:
    name: str
    qtype: int
    qclass: int

@dataclass
class DNSRecord:
    name: str
    rtype: int
    rclass: int
    ttl: int
    rdata: str

class DNSServer:
    def __init__(self, ip: str = '127.0.0.1', port: int = 53):
        self.ip = ip
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((ip, port))
        self.zones = self.load_zones()
        
        # DNS record types
        self.TYPE_A = 1
        self.TYPE_NS = 2
        self.TYPE_SOA = 6
        self.TYPE_AAAA = 28

    def load_zones(self) -> Dict:
        zones = {}
        try:
            zones_dir = os.path.join(os.path.dirname(__file__), 'zones')
            zonefiles = glob.glob(os.path.join(zones_dir, '*.zone'))
            logger.info(f"Found zone files: {zonefiles}")
            
            for zonefile in zonefiles:
                with open(zonefile, 'r') as file:
                    data = json.load(file)
                    origin = data["$origin"]
                    zones[origin] = data
                    logger.info(f"Loaded zone: {origin}")
            
            return zones
        except Exception as e:
            logger.error(f"Error loading zones: {str(e)}")
            return {}

    def get_flags(self, flags: bytes) -> bytes:
        response_flags = bytearray(2)
        response_flags[0] = (1 << 7) | ((flags[0] >> 3) & 0x0F) | (1 << 2)
        response_flags[1] = 0x00
        return bytes(response_flags)

    def decode_domain_name(self, message: bytes, offset: int) -> Tuple[str, int]:
        labels = []
        while True:
            length = message[offset]
            
            if length & 0xC0 == 0xC0:
                pointer = ((length & 0x3F) << 8) | message[offset + 1]
                compressed_name, _ = self.decode_domain_name(message, pointer)
                labels.append(compressed_name)
                offset += 2
                break
            
            if length == 0:
                offset += 1
                break
                
            offset += 1
            labels.append(message[offset:offset + length].decode())
            offset += length
            
        return '.'.join(labels), offset

    def encode_domain_name(self, domain_name: str) -> bytes:
        encoded = bytearray()
        for label in domain_name.split('.'):
            if label:
                encoded.append(len(label))
                encoded.extend(label.encode())
        encoded.append(0)
        return bytes(encoded)

    def encode_soa_rdata(self, soa: Dict) -> bytes:
        rdata = bytearray()
        
        # Encode MNAME (primary nameserver)
        rdata.extend(self.encode_domain_name(soa['mname']))
        
        # Encode RNAME (responsible person's email)
        rdata.extend(self.encode_domain_name(soa['rname']))
        
        # Add the numeric fields
        rdata.extend(int(soa['serial']).to_bytes(4, 'big'))
        rdata.extend(int(soa['refresh']).to_bytes(4, 'big'))
        rdata.extend(int(soa['retry']).to_bytes(4, 'big'))
        rdata.extend(int(soa['expire']).to_bytes(4, 'big'))
        rdata.extend(int(soa['minimum']).to_bytes(4, 'big'))
        
        return bytes(rdata)

    def decode_question(self, data: bytes) -> Tuple[DNSQuestion, int]:
        offset = 12
        qname, offset = self.decode_domain_name(data, offset)
        qtype = int.from_bytes(data[offset:offset + 2], 'big')
        qclass = int.from_bytes(data[offset + 2:offset + 4], 'big')
        return DNSQuestion(qname, qtype, qclass), offset + 4

    def find_record(self, zone: Dict, record_type: str, name: str) -> List[Dict]:
        if record_type not in zone:
            return []
        
        records = []
        for record in zone[record_type]:
            record_name = '' if record['name'] == '@' else record['name']
            query_name = name.replace(zone['$origin'], '').rstrip('.')
            
            if record_name == query_name:
                records.append(record)
        
        return records

    def create_response(self, query_data: bytes) -> Optional[bytes]:
        try:
            transaction_id = query_data[:2]
            question, _ = self.decode_question(query_data)
            logger.info(f"Query for {question.name}, type {question.qtype}")
            
            response = bytearray()
            response.extend(transaction_id)
            response.extend(self.get_flags(query_data[2:4]))
            response.extend(int(1).to_bytes(2, 'big'))  # QDCOUNT = 1
            
            zone = None
            search_domain = question.name + '.' if not question.name.endswith('.') else question.name
            
            for zone_name, zone_data in self.zones.items():
                if search_domain.endswith(zone_name):
                    zone = zone_data
                    break
            
            records = []
            if zone:
                if question.qtype == self.TYPE_A:
                    records = self.find_record(zone, 'a', search_domain)
                elif question.qtype == self.TYPE_AAAA:
                    records = self.find_record(zone, 'aaaa', search_domain)
                elif question.qtype == self.TYPE_NS:
                    records = [{'name': '@', 'ttl': zone.get('$ttl', 3600), 'value': ns['host']} 
                             for ns in zone['ns']]
                elif question.qtype == self.TYPE_SOA and 'soa' in zone:
                    records = [{'name': '@', 'ttl': zone.get('$ttl', 3600), 'soa': zone['soa']}]
            
            response.extend(len(records).to_bytes(2, 'big'))  # ANCOUNT
            response.extend((0).to_bytes(2, 'big'))  # NSCOUNT
            response.extend((0).to_bytes(2, 'big'))  # ARCOUNT
            
            # Add question section
            response.extend(self.encode_domain_name(question.name))
            response.extend(question.qtype.to_bytes(2, 'big'))
            response.extend(question.qclass.to_bytes(2, 'big'))
            
            # Add answer section
            for record in records:
                response.extend(b'\xc0\x0c')  # Name compression
                response.extend(question.qtype.to_bytes(2, 'big'))
                response.extend(question.qclass.to_bytes(2, 'big'))
                response.extend(int(record['ttl']).to_bytes(4, 'big'))
                
                if question.qtype == self.TYPE_A:
                    response.extend((4).to_bytes(2, 'big'))
                    for octet in record['value'].split('.'):
                        response.append(int(octet))
                        
                elif question.qtype == self.TYPE_AAAA:
                    response.extend((16).to_bytes(2, 'big'))
                    parts = record['value'].split(':')
                    if '' in parts:
                        idx = parts.index('')
                        missing = 8 - (len(parts) - 1)
                        parts = parts[:idx] + ['0'] * missing + parts[idx+1:]
                    for part in parts:
                        if part == '':
                            part = '0'
                        value = int(part, 16)
                        response.extend(value.to_bytes(2, 'big'))
                        
                elif question.qtype == self.TYPE_NS:
                    rdata = self.encode_domain_name(record['value'])
                    response.extend(len(rdata).to_bytes(2, 'big'))
                    response.extend(rdata)
                    
                elif question.qtype == self.TYPE_SOA:
                    rdata = self.encode_soa_rdata(record['soa'])
                    response.extend(len(rdata).to_bytes(2, 'big'))
                    response.extend(rdata)
            
            return bytes(response)
            
        except Exception as e:
            logger.error(f"Error creating response: {str(e)}", exc_info=True)
            return None

    def run(self):
        logger.info(f"DNS Server running on {self.ip}:{self.port}")
        while True:
            try:
                data, addr = self.sock.recvfrom(512)
                logger.info(f"Received query from {addr}")
                
                response = self.create_response(data)
                if response:
                    self.sock.sendto(response, addr)
                    logger.info(f"Sent response to {addr}")
                else:
                    logger.error("Failed to create response")
                    
            except Exception as e:
                logger.error(f"Error handling request: {str(e)}", exc_info=True)

if __name__ == "__main__":
    server = DNSServer()
    server.run()