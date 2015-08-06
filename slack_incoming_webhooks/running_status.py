from core import (Field, Attachment, Message)
import os
import datetime
import time
from keys import POST_URL
import psutil

class TimeSinceRestartField(Field):
    def __init__(self):
        super(TimeSinceRestartField, self).__init__("Time since restart", self.time_since_restart(), short=True)

    def time_since_restart(self):
        return str(datetime.datetime.now() - datetime.datetime.fromtimestamp(psutil.boot_time()))

class CPUField(Field):
    def __init__(self):
        super(CPUField, self).__init__("CPU Usage", self.cpu_usage(), short=True)

    def cpu_usage(self):
        return str(psutil.cpu_percent()) + '%'

class MemoryField(Field):
    def __init__(self):
        super(MemoryField, self).__init__("Memory Usage", self.memory_usage(), short=True)

    def memory_usage(self):
        return str(psutil.phymem_usage().percent) + '%'

class DiskField(Field):
    def __init__(self):
        super(DiskField, self).__init__("Disk Usage", self.disk_usage(), short=True)

    def disk_usage(self):
        return str(psutil.disk_usage('/').percent) + '%'

class SystemUsageAttachment(Attachment):

    def __init__(self):
        fs = [TimeSinceRestartField(), CPUField(), MemoryField(), DiskField()]
        super(SystemUsageAttachment, self).__init__("System Usage", "good", fields=fs)

class ProcessReportAttachment(Attachment):

    def __init__(self, number=10):
        super(ProcessReportAttachment, self).__init__(self, "Process Report", text=self.process_report(number))

    def process_report(self, number=None):

        def fixed_length(s, length):
            padding = ' ' * (length - len(s)) if len(s) < length else ''
            return s[:length] + padding

        ps = sorted(
            [(
                p.name(),
                p.username(),
                '{}%'.format(p.get_cpu_percent()),
                '{}%'.format(p.get_memory_percent()))
            for p in psutil.get_process_list()],
            key=lambda p: p[2], reverse=True)[:number]
        lengths = [12, 8, 6, 6]
        string = """```Process Name  User      CPU     Memory \n""" +\
        """------------  --------  ------  ------\n"""

        for p in ps:
            s = ''.join([fixed_length(str(s), l) + '  ' for s, l in zip(p, lengths)]) + '\n'
            string += s
        return string + '```'

    def to_dict(self):
        d = super(ProcessReportAttachment, self).to_dict()
        d["mrkdwn_in"] = ["text"]
        return d

def restart_required():
    return os.path.exists('/var/run/reboot-required')

def main_loop(name="Calculon", channel="#servers", emoji=":calculon:"):

    while True:
        attachments = [
            SystemUsageAttachment(),
            ProcessReportAttachment()
        ]
        if restart_required():
            attachments.insert(0, Attachment("Restart Required", "warning"))

        m = Message('Running status:', time.ctime(), emoji=emoji, attachments=attachments)
        m.send(POST_URL, username=name, channel=channel)
        time.sleep(60 * 60 * 6)

if __name__ == '__main__':
    main_loop()
