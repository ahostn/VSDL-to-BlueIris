from flask import Flask
from flask_socketio import SocketIO
import sys, os.path, time, logging
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
import threading
import requests

#
# VSDL monitoring by Andrej Hostnikar
# (C)2015
#
# Web server ni zagnan, po potrebi spremeni parametre, sicer zaženi iz konzole
#
# Zadnja sprememba: 28.9.2o19 

app = Flask(__name__)
socketio = SocketIO(app)

@app.route("/")
def hello():
    return "Vremenska postaja Spodnji Slemen; vreme.htm monitoring"

class MyEventHandler(PatternMatchingEventHandler):
	#def on_moved(self, event):
		#super(MyEventHandler, self).on_moved(event)
		#logging.info("File %s was just moved" % event.src_path)

	#def on_created(self, event):
		#super(MyEventHandler, self).on_created(event)
		#logging.info("File %s was just created" % event.src_path)

	#def on_deleted(self, event):
		#super(MyEventHandler, self).on_deleted(event)
		#logging.info("File %s was just deleted" % event.src_path)

	def on_modified(self, event):
		super(MyEventHandler, self).on_modified(event)
		logging.info("\n\rZaznana spremeba datoteke %s ... odpiram za parsing!" % event.src_path)
		print("Čakam 3s ...")
		time.sleep(3)		
		with open(event.src_path,'r') as f:
			for line in f:
				data = line.split('|')
				
				if len(data) > 10:
					try:
						# poveži se na viltuš API in dobi podatke iz glavnega senzorja (id=11)
						r = requests.get('http://ping.viltus.info/api.php?id=011&tempOnly=1')
						api = r.text
						api = api.split('|') 
						print(api)
					except Exception as e:
						print("PING API je nedosegljv!"+str(e))
						api[0]='---'
						api[1]='---'
						
					print('Trenutno je %s stopinj C.' % format(api[0])) 
					print('Piha veteer s hitrostjo %s hm/h.' % format(data[4])) 
					print('Smer vetra: %s stopinj.' % format(data[6])) 
					print('Vlaga je %s %%. ' % format(api[1]))
					
					if data[12]!='---':	
						print('Dežja v zadnji uri: %s mm.' % format(data[12]))
					else:
						print('Senzor za dež se ne odziva!')
					# shrani podatke v bi.txt, ki jih bere BlueIris ... nastavit za vsako kamero posebej
					with open('d:/vreme/blueiris.txt','w') as bi:
						trenutniCajt = time.localtime()
						ura = time.strftime("%H:%M\n%d.%m.%y", trenutniCajt) #nastavi uro v normano obliko
						bi.write(api[0]+"°C\n"+api[1]+"%\n"+data[12]+" mm/u\n"+data[13]+" mm/d\n"+data[11]+" mm/r\n"+ura)
						bi.close()
						print("Podatki shranjeni na D:/vreme/blueiris.txt")
					print('\n\r\n\r')	
		f.close()			
""" 
	podatki shranjeni iz vremenske postaje morajo biti v obliki:
	<!-- RAW |3,7|1020,0|Rainy|5,4|7,6|250|78,0|10. december 2009|20:59|Night|0|0|0|0:53|12:29|1.1.2010|-0,38|0| AHVP -->     
	<!-- RAW |[Temperature1]|[SlpBarometer]|[StationForecast]|[GustSpeed]|[GustMax0]|[Direction]|[RH1]|[date]|[time]|[DayNight]|[RainRate]|[RainThisHour]|[RainThisDay]|[MoonRise]|[MoonSet]|[FullMoon]|[QnhRate]|[Uv]|[AppTemp1]|[TempRate1]|[DewPoint1]|[WindChill1]|[annualrain]|[RH8]|[Temperature8]|[RH10]|[Temperature10]|[Temperature0]|[RH0]|[Rain-1]|[Rain-2]|[Temp1Min0]|[Temp1Max0]|[Temp1Min-1]|[Temp1Max-1]|[Temp1Min-2]|[Temp1Max-2]|[CumTemp1Min-7]|[CumTemp1Max-7]| AHVP -->
	
	0 RAW|
	1 [Temperature1]
	2 [SlpBarometer]|
	3 [StationForecast]|
	4 [GustSpeed]|
	5 [GustMax0]|
	6 [Direction]|
	7 [RH1]|
	8 [date]|
	9 [time]|
	10 [DayNight]|
	11 [RainRate]|
	12 [RainThisHour]|
	13 [RainThisDay]|
	14 [MoonRise]|
	15 [MoonSet]|
	16 [FullMoon]|
	17 [QnhRate]|
	18 [Uv]|
	19 [AppTemp9]|
	20 [TempRate1]|
	21 [DewPoint9]|
	22 [WindChill9]|
	23 [annualrain]|
	24 [RH9]|
	25 [Temperature9]|
	26 [RH5]|
	27 [Temperature5]|
	28 [Temperature0]|
	29 [RH0]|
	30 [Rain-1]|
	31 [Rain-2]|
	32 [Temp1Min0]|
	33 [Temp1Max0]|
	34 [Temp1Min-1]|
	35 [Temp1Max-1]|
	36 [Temp1Min-2]|
	37 [Temp1Max-2]|
	38 [CumTemp1Min-7]|
	39 [CumTemp1Max-7]| 
	40 AHVP -->    Andrej Hostnikar Vpremenska Postaja -- ne spreminjaj sicer ne bo delala slika.php za vreme
"""	
def monitor(file_path=None):
    logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(message)s',datefmt='%d-%m-%Y %H:%M:%S')
    watched_dir = os.path.split(file_path)[0]
   
    patterns = [file_path]
   
    event_handler = MyEventHandler(patterns=patterns)
    observer = Observer()
    observer.schedule(event_handler, watched_dir, recursive=True)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print('Monitoring prekinjen.')
    observer.join()

if __name__ == "__main__":
	print("Zaganjam monitoring za vreme.htm ...")
	if len(sys.argv) > 1:
		
		path = sys.argv[1]
		monitor(file_path=path.strip())
		# tu vklopi, če rabiš web server za nadzor
		#socketio.run(app, host='0.0.0.0', port=80, debug=True, threaded=True)
		
	else:
		print ('Izberi datoteko za monitoring')
