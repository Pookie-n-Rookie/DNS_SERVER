# DNS Server
# What is a DNS server?
A DNS server (Domain Name System server) is a system that translates human-readable domain names (like www.example.com) into machine-readable IP addresses (like 93.184.216.34). The DNS server acts as a "phonebook" of the internet, enabling users to access websites and other resources without needing to remember IP addresses.



# There are 4 DNS servers involved in loading a webpage:
## DNS recursor: 
The recursor can be thought of as a librarian who is asked to go find a particular book somewhere in a library. The DNS recursor is a server designed to receive queries from client machines through applications such as web browsers. Typically the recursor is then responsible for making additional requests in order to satisfy the client’s DNS query.
## Root nameserver :
The root server is the first step in translating (resolving) human readable host names into IP addresses. It can be thought of like an index in a library that points to different racks of books - typically it serves as a reference to other more specific locations.
## TLD nameserver:
The top level domain server (TLD) can be thought of as a specific rack of books in a library. This nameserver is the next step in the search for a specific IP address, and it hosts the last portion of a hostname (In example.com, the TLD server is “com”).
## Authoritative nameserver:
This final nameserver can be thought of as a dictionary on a rack of books, in which a specific name can be translated into its definition. The authoritative nameserver is the last stop in the nameserver query. If the authoritative name server has access to the requested record, it will return the IP address for the requested hostname back to the DNS Recursor (the librarian) that made the initial request.




## Request message format
All DNS messages have the same format:
```text
               +---------------------+
               |        Header       |
               +---------------------+
               |       Question      | the question for the name server
               +---------------------+
               |        Answer       | Resource Records (RRs) answering the question
               +---------------------+
               |      Authority      | RRs pointing toward an authority
               +---------------------+
               |      Additional     | RRs holding additional information
               +---------------------+
               Query and request messages fill out different parts of the message. Our query will contain the Header and Question sections.
```
              
# Header
             The header has the following format:

```text
      0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
      |                      ID                       |
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
      |QR|   Opcode  |AA|TC|RD|RA|   Z    |   RCODE   |
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
      |                    QDCOUNT                    |
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
      |                    ANCOUNT                    |
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
      |                    NSCOUNT                    |
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
      |                    ARCOUNT                    |
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+

```
In this diagram, each cell represents a single bit. In each row, there are sixteen columns, representing two bytes of data. The diagram is split into rows to make it easier to read, but the actual message is a continuous series of bytes.

As both queries and responses share a header format, some of the fields aren't relevant to our query, and will be set to 0. A full desciption of each of these fields can be found in RFC1035 Section 4.1.1.

The fields which are relevant to us are:

ID: An arbitrary 16 bit request identifier. The same ID is used in the response to the query so we can match them up. Let's go with AA AA.

QR: A 1 bit flag specifying whether this message is a query (0) or a response (1). As we're sending a query, we'll set this bit to 0.

Opcode: A 4 bit field that specifies the query type. We're sending a standard query, so we'll set this to 0. The possibilities are: - 0: Standard query - 1: Inverse query - 2: Server status request - 3-15: Reserved for future use

TC: 1 bit flag specifying if the message has been truncated. Our message is short, and won't need to be truncated, so we can set this to 0.

RD: 1 bit flag specifying if recursion is desired. If the DNS server we send our request to doesn't know the answer to our query, it can recursively ask other DNS servers. We do wish recursion to be enabled, so we will set this to 1.

QDCOUNT: An unsigned 16 bit integer specifying the number of entries in the question section. We'll be sending 1 question.

Full header
Combining these fields, we can write out our header in hexadecimal:

AA AA - ID
01 00 - Query parameters
00 01 - Number of questions
00 00 - Number of answers
00 00 - Number of authority records
00 00 - Number of additional records
To get the query parameters, we concatenate the values of the fields QR to RCODE, remembering that fields not mentioned above are set to 0. This gives 0000 0001 0000 0000, which is 01 00 in hexadecimal. This represents a standard DNS query.

# Question
The question section has the format:
```text
      0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
      |                                               |
      /                     QNAME                     /
      /                                               /
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
      |                     QTYPE                     |
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
      |                     QCLASS                    |
      +--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+--+
```
QNAME: This contains the URL who's IP address we wish to find. It is encoded as a series of 'labels'. Each label corresponds to a section of the URL. The URL example.com contains two sections, example, and com.

To construct a label, we URL-encode the section, producing a series of bytes. The label is that series of bytes, preceded by an unsigned integer byte containing the number of bytes in the section. To URL-encode our URL, we can just lookup the the ASCII code for each character.

The QNAME section is terminated with a zero byte (00).

QTYPE: The DNS record type we're looking up. We'll be looking up A records, whose value is 1.

QCLASS: The class we're looking up. We're using the the internet, IN, which has a value of 1.


 ## Overview

This DNS server is a simple implementation of a DNS server that processes DNS queries and provides responses based on zone data. It supports common DNS record types like A, AAAA, NS, and SOA, and can handle both standard queries and reverse lookups.

## Functionality

This server listens for DNS queries, processes them, and responds with the appropriate DNS records, based on the zone data available. The server supports standard DNS query types, including A (host address), AAAA (IPv6 address), NS (name server), and SOA (start of authority).

The DNS query and response structure follows the format outlined in RFC 1035, where the request is divided into the header and question sections, and the response includes the answer, authority, and additional sections.

### Features
- Handles Common Record Types: A, AAAA, NS, SOA.
- Supports Reverse Lookups: Based on the zone data provided.
- Query Resolution: Resolves queries against configured zones.
# Installation and Usage
## Step 1: Clone the Repository
```bash
Copy code
git clone https://github.com/your-repo-url.git
```



