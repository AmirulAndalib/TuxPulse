
#!/usr/bin/env python3
import subprocess, shutil, dbus, dbus.service, dbus.mainloop.glib
from gi.repository import GLib

SERVICE="org.eoliann.TuxPulse"
PATH="/org/eoliann/TuxPulse"
IFACE="org.eoliann.TuxPulse"

def pm():
    for p in ("apt","pacman","dnf","zypper"):
        if shutil.which(p): return p
    return None

def run(cmd):
    r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    if r.returncode!=0: raise Exception(r.stdout)
    return r.stdout

class H(dbus.service.Object):
    def __init__(self,b): super().__init__(b,PATH); self.p=pm()

    @dbus.service.method(IFACE,out_signature="s")
    def Update(self):
        return run({"apt":["apt","update"],
                    "pacman":["pacman","-Sy"],
                    "dnf":["dnf","makecache"],
                    "zypper":["zypper","refresh"]}[self.p])

def main():
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    b=dbus.SystemBus()
    dbus.service.BusName(SERVICE,b)
    H(b)
    GLib.MainLoop().run()

if __name__=="__main__": main()
