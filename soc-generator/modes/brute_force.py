import datetime
from formats.firewall import generate_firewall_log
from formats.siem import generate_siem_log

def generate_brute_force_sequence(attacker_ip="198.51.100.99",target_host="host01"):
    events = []
    now = datetime.datetime.now()

    for i in range(8):
        event_time = now + datetime.timedelta(seconds=i *2)
        fw_payload = generate_firewall_log(event_time,attacker_ip,"10.0.0.15",49152 +i,22,action="BLOCK")
        events.append((event_time, "firewall","fw01",fw_payload))

        siem_payload = generate_siem_log(event_time,target_host,"root",attacker_ip,49152+i,status="Failed")
        events.append((event_time,"siem",target_host,siem_payload))
    return events
