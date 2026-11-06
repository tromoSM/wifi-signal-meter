from time import sleep
from subprocess import check_output,CalledProcessError
from re import search
from keyboard import is_pressed
from matplotlib import pyplot
from matplotlib.animation import FuncAnimation
from numpy import arange,pi,sin,linspace,array
from scipy.interpolate import make_interp_spline
from sys import argv
from xdialog import yesno,YES,warning
# Source - https://stackoverflow.com/a/55023273
# Posted by Suman Saurabh, modified by community. See post 'Timeline' for change history
# Retrieved 2026-11-05, License - CC BY-SA 4.0

livemode=False
if len(argv)>1:
    for arg in argv[1:]:
        if arg=='live':
            livemode=True

f,a=pyplot.subplots()
if livemode:
    print('>> script is running in live mode')
    pyplot.ion()
    line,=a.plot([],[])
    a.set_ylim(0,100)
    a.set_xlim(0,60)
    a.grid(True)
    pyplot.show(block=False)

infobox=dict(
    boxstyle="round,pad=0.5",
    alpha=0
)
signalleveltext=a.text(0.05,0.1,'SIGNAL : NO SIGNAL',transform=a.transAxes,verticalalignment='baseline',horizontalalignment='left',bbox=infobox)
ssidtext=a.text(0.05,0.15,'SSID : NONE',transform=a.transAxes,verticalalignment='baseline',horizontalalignment='left',bbox=infobox)
colors={
    'low':'orange',
    "extra low":'red',
    "no signal":'dodgerblue',
    'error':'brown',
    'normal':'gold',
    "high":'lawngreen',
    "extra high":"springgreen",
    "none":"black"
}

pyplot.title('signal strength')
pyplot.xlabel('time')
pyplot.ylabel('signal strength %')

old=0
laster=None
signallist=[]
points=0
lastssid=''
wifichanged=False
Running=True
ssidlist=[]
lastssider=False
levelinfo='none'

def getsignallevel(finalcount,outputav):
    if 80>finalcount>50:
        signallevel='normal'
    elif 95>finalcount>80:
        signallevel='high'
    elif finalcount>95:
        signallevel='extra high'
    elif finalcount<50:
        signallevel='low'
    elif finalcount<25:
        signallevel='extra low'
    elif finalcount==0:
        signallevel=='no signal'
    if not outputav:
        signallevel='error'
    return signallevel
def status():
    global old,laster,points,wifichanged,Running,lastssid,lastssider,levelinfo
    # Source - https://stackoverflow.com/a/39463881
    # Posted by gmag11, modified by community. See post 'Timeline' for change history
    # Retrieved 2026-11-05, License - CC BY-SA 3.0
    try:
        output=check_output(["netsh", "wlan", "show", "network", "mode=Bssid"],text=True)
    except CalledProcessError as er:
        if laster!=er.returncode:
            laster=er.returncode
            print(f'Error when checking wifi signal check. returncode : {laster}. Check your internet connection and try again')
        output=None
    finalcount=0
    ssid=None
    if output:
      try:
        ssid=search(r'SSID 1\s*:\s*(.+)',output)
        if ssid and ssid.group(1):
          if lastssid!='' and ssid.group(1)!=lastssid and ssid.group(1).split(':')[0].replace(' ','')!='NetworkType':
            wifichanged=True
            if ssid.group(1) not in ssidlist:
                ssidlist.append(ssid.group(1))
            if livemode:
               answer=yesno('Wifi',f'Wifi network changed from {lastssid} to {ssid.group(1)}. Do you want to continue ?')
               if answer!=YES:
                  Running=False
            lastssid=ssid.group(1)
          elif ssid.group(1).split(':')[0].replace(' ','')=='Networktype':
            if not lastssider:
                print(f'Network SSID couldnt be found : ({" : ".join(ssid.group(1).split(':')).strip()})')
                lastssider=True
          elif ssid.group(1) not in ssidlist:
                ssidlist.append(ssid.group(1))
                lastssid=ssid.group(1)
        output=search(r'Signal\s*:\s*(\d+)%',output)
        outputav=True
        finalcount=output.group(1)
      except Exception as er:
        if laster!=er:
            print(er)
        outputav=False
    else:
        outputav=False

    signallevel='none'
    finalcount=int(finalcount)
    signallevel=getsignallevel(finalcount,outputav)
    if livemode:
        line.set_color(colors[signallevel.lower()])
    levelinfo=signallevel
    signalleveltext.set_text(f'SIGNAL : {signallevel.upper()}')
    ssidtext.set_text(f'SSID : {lastssid.upper()}')
    print(f'signal{(" ("+lastssid+") ") if lastssid!='' else ""}: {finalcount} {('↑' if int(finalcount)>=old else "↓") if outputav else "×"}'.ljust(20+len(lastssid)),sep='',end="\r",flush=True)
    old=int(finalcount)
    points+=1
    signallist.append(old)

print('press Esc to stop and see the results')
while Running:
    if is_pressed('esc'):
        print(''.ljust(20+len(lastssid)),sep='',end='\r',flush=True)
        break
    status()
    if livemode:
        x=arange(len(signallist))
        y=array(signallist)
        xy=make_interp_spline(x,y,k=min(3,len(x)-1))
        X=linspace(x.min(), x.max(), 5000)
        Y=xy(X)
        line.set_data(X,Y)
        a.set_xlim(max(0,len(signallist)-60),max(60,len(signallist)))
        f.canvas.draw_idle()
        f.canvas.flush_events()

if not livemode:
    print('loading results...')
    average=sum(signallist)/len(signallist)
    signalleveltext.set_text(f'SIGNAL : {getsignallevel(average,True).upper()}')
    ssidtxt=lastssid
    if wifichanged:
        ssidtxt=' | '.join(ssidlist)
    ssidtext.set_text(f'SSID : {ssidtxt.upper()}')
    x=arange(len(signallist))
    y=array(signallist)
    xy=make_interp_spline(x, y)
    X=linspace(x.min(), x.max(), 5000)
    Y=xy(X)
    pyplot.plot(X,Y)
    pyplot.ylim(min(signallist),max(signallist))
    pyplot.grid(True)
    if wifichanged:
        warning('Wifi',f'Wifi network changed while measuring signal. Results might be from different networks\n\nNetworks : {','.join(ssidlist)}')
    pyplot.show()