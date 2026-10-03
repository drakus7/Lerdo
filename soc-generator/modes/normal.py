import random
import datetime
from formats.firewall import generate_firewall_log
from formats.siem import generate_siem_log
from formats.ids import generate_ids_log

# Make sure this name matches what you use below
PUBLIC_IPS = ["203.0.113.45", "198.51.100.22", "192.0.2.14", "45.33.32.156"]
INTERNAL_IPS = ["10.0.0.12", "10.0.0.15", "10.0.0.50"]
HOSTS = ["host01", "host02", "host03"]
USERS = ["root", "admin", "ubuntu", "sysop"]

def generate_normal_event():
    now = datetime.datetime.now()
    source_type = random.choice(["firewall", "siem", "ids"])
    
    if source_type == "firewall":
        src = random.choice(PUBLIC_IPS) # Ensure this matches the variable name above!
        dst = random.choice(INTERNAL_IPS)
        spt = random.randint(1024, 65535)
        dpt = random.choice([22, 80, 443])
        payload = generate_firewall_log(now, src, dst, spt, dpt, action="ALLOW" if dpt in [80, 443] else "BLOCK")
        host = "fw01"
    elif source_type == "siem":
        src = random.choice(PUBLIC_IPS)
        host = random.choice(HOSTS)
        user = random.choice(USERS)
        port = random.randint(1024, 65535)
        payload = generate_siem_log(now, host, user, src, port, status="Success" if random.random() > 0.3 else "Failed")
    else:
        src = random.choice(PUBLIC_IPS)
        dst = random.choice(INTERNAL_IPS)
        payload = generate_ids_log(now, src, dst, signature="ET INFO Standard Outbound Connection")
        host = "suricata01"

    return (now, source_type, host, payload)