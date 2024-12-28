 ## Overview
This DNS server is a simple implementation of a DNS server that processes DNS queries and provides responses based on zone data. It supports common DNS record types like A, AAAA, NS, and SOA, and can handle both standard queries and reverse lookups.

## Functionality

This server listens for DNS queries, processes them, and responds with the appropriate DNS records, based on the zone data available. The server supports standard DNS query types, including A (host address), AAAA (IPv6 address), NS (name server), and SOA (start of authority).

The DNS query and response structure follows the format outlined in RFC 1035, where the request is divided into the header and question sections, and the response includes the answer, authority, and additional sections.

## Features
### mydns.py
- Handles Common Record Types: A, AAAA, NS, SOA.
- Supports Reverse Lookups: Based on the zone data provided.
- Query Resolution: Resolves queries against configured zones.
### dns_enumeration.py
- returns various important information about the target like DNS record types, host names, IP addresses and much more depending upon the configuration of that target system.

# Setting Up the Python Environment

This guide will help you set up a Python virtual environment and install the required dependencies from the `requirement.txt` file. 

## Prerequisites

- **Python 3.7+** must be installed on your system.
- **pip** (Python's package manager) should be available.

## Steps

###Clone the Repository

First, clone the repository from GitHub:

```bash
git clone <repository_url>
cd <repository_directory>
```
Replace <repository_url> with your repository URL and <repository_directory> with the name of the folder created.
### Create a Virtual Environment
Run the following command to create a virtual environment:
```bash
python -m venv venv
```
This will create a virtual environment named venv in the current directory.
### Activate the Virtual Environment
Windows:
```bash
venv\Scripts\activate
```
macOS/Linux:
```bash
source venv/bin/activate
```
### Install Dependencies
After activating the virtual environment, install the required dependencies:

```bash
pip install -r requirement.txt
```
## Start the DNS server:

```bash
python mydns.py
```

Open another terminal and use nslookup to test:

```bash

# Query default A record for example.com
nslookup example.com 127.0.0.1

# Query specific record types
nslookup -type=a example.com 127.0.0.1
nslookup -type=aaaa example.com 127.0.0.1
nslookup -type=soa example.com 127.0.0.1
nslookup -type=ns example.com 127.0.0.1

# Query subdomain (e.g., www.example.com)
nslookup www.example.com 127.0.0.1
```
## Run the enumeration script:

```bash
python enumeration.py

enter the domain:< enter as you desire >
```
# Testing:

### Explanation of mydns.py

https://github.com/user-attachments/assets/39a72657-db8b-4ba6-b011-082333783cd1



### Explanation of dns_enumeration.py

https://github.com/user-attachments/assets/92eb43aa-aecc-4e0e-9b2f-672ea216c727



## References

1. **RFC 1035** - Domain Names - Implementation and Specification: [Read Here](https://datatracker.ietf.org/doc/html/rfc1035)  
2. **Hand-Writing DNS Messages** by Routley: [Read Here](https://routley.io/posts/hand-writing-dns-messages)
3. **Python DNS TOOLKIT**:[Read Here](https://pypi.org/project/dnspython/)


## Disclaimer
This project is made for educational purposes only. It is intended to demonstrate how a DNS server operates and should not be used in production environments. Always ensure security and compliance when dealing with network services.










