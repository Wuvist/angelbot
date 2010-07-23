import tail
import os
from stat import *
import datetime
import sys
import time
import urllib
import urllib2

def fetch_page (url):
    data = None
    try:
        req = urllib2.Request(url, data)
        response = urllib2.urlopen(req)
        result = response.read()
    except:
        return ""
    return result

d = datetime.date.today()
max_usage = 85
log_files = [
    sys.argv[1] + d.isoformat().replace("-", "")[2:] + ".log"
]

def add (data, key):
    if data.has_key(key):
        data[key] = data[key] + 1
    else:
        data[key] = 1

def get_cpu_load():
    """ Returns a list CPU Loads"""
    result = []
    cmd = "WMIC CPU GET LoadPercentage "
    response = os.popen(cmd + ' 2>&1','r').read().strip().split("\r\n")
    for load in response[1:]:
       result.append(int(load))

    # Get average
    if len(result) == 0:
	result = [0]

    return  sum(result) / len(result)

def check_logs ():
    for log_file in log_files:
        codes = {"ok":0, "error":0}
        try:
            f = file("lastupdate.txt")
            last_modified_on = f.read()
            f.close()
        except:
            last_modified_on = ""        
        

        ls = tail.tail(log_file, 1000)
        first_time = None
        last_time = ""
        for i in range(1, len(ls)):
            l = ls[-i]
            if l.startswith("201"):            
                modified_on = l[0:19]
                f = file("lastupdate.txt", "w")
                f.write(modified_on)
                f.close()
                
                modified_on = datetime.datetime.strptime(modified_on, "%Y-%m-%d %H:%M:%S")
                modified_on = time.mktime(modified_on.timetuple())

                break


        codes["modified_on"] = int(modified_on) +28800
        print codes["modified_on"]
        time_takens = []

        total = len(ls)
        for l in ls:
            if l.startswith("201") and l[0:19] > last_modified_on:
                data = l.split(" ")
                if not first_time:
		            first_time = l[0:19]
                
                last_time = l[0:19]

                try:
                    code = data[-3]
                    code = int(code)
                    if code < 400:
                        add(codes, "ok")
                    else:
                        add(codes, "error")

                    time_taken = int(data[-1])
                    time_takens.append(time_taken)
                except:
                    pass

        cpu = get_cpu_load()
        if cpu >= max_usage:
            time.sleep(2)
            cpu = get_cpu_load()

        codes["cpu"] = cpu
        codes["date"] = time.strftime("%Y-%m-%d %H:%M:%S")
        if len(time_takens) > 0:        
            codes["max_time"] = max(time_takens)
            codes["min_time"] = min(time_takens)
            codes["avg_time"] = sum(time_takens) /  len(time_takens)
            codes["requests"] = len(time_takens)
            first_time = datetime.datetime.strptime(first_time, "%Y-%m-%d %H:%M:%S")
            last_time = datetime.datetime.strptime(last_time, "%Y-%m-%d %H:%M:%S")
            duration = last_time - first_time
            codes["requests"] = len(time_takens) / duration.seconds


        data = str(codes).replace("'", '"')
        f = file(sys.argv[2], "w+")
        f.write(data)
        f.close()

        print data

        logs = file(d.isoformat() + ".log", "a")
        logs.write(data)
        logs.write("\n")
        logs.close()

        has_error = False
        if codes["error"] > 200 or codes["avg_time"] > 1000 or codes["requests"] < 2 or codes["cpu"] > 85:
            has_error = True
        f = file("update.bat", "w+")
        if has_error:
            #f.write("iisapp /a mobileshabik.morange.com /r")

            logs = file("errlog" + str(modified_on) + ".log", "w+")
            logs.writelines(ls)
            logs.close()
        f.write("\n")
        f.write("update_stat.bat")
        f.close()

        rate = float(codes["ok"]) / (float(codes["ok"]) + float(codes["error"]))
        url = "http://angel:8080/rrd?rrd=mobileweb163&ds=online&v=%s&v=%s&v=%s&v=%s" % (str(rate), str(codes["cpu"]), str(codes["avg_time"]), str(codes["requests"]))
        print url

        fetch_page(url)

if __name__ == "__main__":
    check_logs()