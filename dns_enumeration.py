import dns.resolver
import logging

logging.basicConfig(level=logging.INFO)


def query_dns_records(domain, record_types, timeout=5.0, lifetime=15.0):
    resolver = dns.resolver.Resolver()
    resolver.timeout = timeout  
    resolver.lifetime = lifetime 
    results = {}

    for record_type in record_types:
        try:
            logging.info(f"Querying {record_type} records for {domain}...")
            answers = resolver.resolve(domain, record_type)
            results[record_type] = [str(rdata) for rdata in answers]
            logging.info(f"Found {record_type} records for {domain}.")
        except dns.resolver.NoAnswer:
            logging.warning(f"No {record_type} records found for {domain}.")
        except dns.resolver.NXDOMAIN:
            logging.error(f"Domain {domain} does not exist.")
            break
        except dns.resolver.LifetimeTimeout:
            logging.error(f"Query for {record_type} records of {domain} timed out.")
        except Exception as e:
            logging.error(f"Error querying {record_type} records for {domain}: {e}")

    return results


if __name__ == "__main__":
    target_domain = input("Enter domain: ").strip()
    record_types = ["A", "AAAA", "CNAME", "MX", "NS", "SOA"]

    results = query_dns_records(target_domain, record_types)


    for record_type, records in results.items():
        print(f"{record_type} records for {target_domain}:")
        for record in records:
            print(f"  {record}")
