import datetime

def generate_siem_log(timestamp: datetime.datetime, host: str, user: str, src_ip: str, port: int, status: str = "Failed") -> str:
    # Example: Sep 22 03:14:07 host01 sshd[1234]: Failed password for root from 203.0.113.45 port 51322 ssh2
    ts_str = timestamp.strftime("%b %d %H:%M:%S")
    if status == "Failed":
        return f"{ts_str} {host} sshd[1234]: Failed password for {user} from {src_ip} port {port} ssh2"
    else:
        return f"{ts_str} {host} sshd[1234]: Accepted password for {user} from {src_ip} port {port} ssh2"
