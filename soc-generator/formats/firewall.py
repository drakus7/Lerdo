import datetime

def generate_firewall_log(timestamp:datetime.datetime,src_ip:str,dst_ip:str,spt:int,dpt:int,action:str ="BLOCK") -> str:
    # Example: Sep 22 03:14:07 fw01 kernel: BLOCK IN=eth0 OUT= SRC=203.0.113.45 DST=10.0.0.12 PROTO=TCP SPT=51322 DPT=22
    ts_str = timestamp.strftime("%b %d %H:%M:%S")
    return f"{ts_str} fw01 kernel: {action} IN=eth0 OUT= SRC={src_ip} DST={dst_ip} PROTO=TCP SPT={spt} DPT={dpt}"
