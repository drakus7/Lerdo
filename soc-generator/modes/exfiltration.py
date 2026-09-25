import datetime
from formats.ids import generate_ids_log
from formats.firewall import generate_firewall_log

def generate_exfiltration_sequence(attacker_ip="203.0.113.88", internal_ip="10.0.0.50"):
    events = []
    now = datetime.datetime.now()
    
    for i in range(4):
        event_time = now + datetime.timedelta(seconds=i * 5)
        ids_payload = generate_ids_log(event_time, internal_ip, attacker_ip, signature="ET POLICY Suspicious Outbound Data Transfer")
        events.append((event_time, "ids", "suricata01", ids_payload))
        
        fw_payload = generate_firewall_log(event_time, internal_ip, attacker_ip, 443, 9001, action="ALLOW")
        events.append((event_time, "firewall", "fw01", fw_payload))
        
    return events
