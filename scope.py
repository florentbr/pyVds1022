from queue import Queue
from threading import Thread
from vds1022  import VDS1022 
import time

# Scope is the interface the application talks to.
# The reason for this is that to ensure proper scope operation it must be continually polled (for some reason)
def runThread(scope,cmdQueue,outQueue):
    try:
        scope.capture_init()
        while True:
            if not cmdQueue.empty():
                (cmd,args) = cmdQueue.get()
                if cmd == 'configure_timebase':
                    scope.configure_timebase(args[0])
                elif cmd == 'configure_channel':
                    scope.configure_channel(args[0])
                elif cmd == 'capture_init':
                    scope.capture_init()
                elif cmd == 'capture_start':
                    scope.capture_start()
                    outQueue.put([ [],[] ])
                elif cmd ==  'get_data':
                    print("waiting for data ready")
                    timeout = time.time() + 3
                    timedOut = False
                    while scope.get_data_ready() == 0:
                        if timeout < time.time():
                            timedOut = True
                            break
                    if not timedOut:
                        print("Data ready")
                        outQueue.put(scope.get_data())
                    else:
                        print("Timedout")
                        scope.force_trigger()
                        outQueue.put([ [],[] ])
                elif cmd == 'trg_pre':
                    scope.configure_trg_pre(args[0])
                elif cmd == 'trg_suf':
                    scope.configure_trg_suf(args[0])
                elif cmd == 'close':
                    break
                else:
                    print("Received an unknown command",cmd)
                    break

            else:
                # Wait 10ms so as not to use too much CPU time.
                time.sleep(0.01)
                scope.checkBitstreamUpload()

    except Exception as e:
        print("Exception in thread",e)
    scope.close()

class Scope():
    def __init__(self,
            voltage=[7,1],
            lowpass=[0,0],
            coupling=[0,0],
            channelOn=[True,False],
            timebase = 0x190,
            trg_suf=5000,
            trg_pre=0,
            ):
   
        print("making a scope")
        self.scope = VDS1022(voltage,lowpass,coupling,channelOn,timebase,trg_suf,trg_pre)
        print("made a scope")

        self.cmdQueue = Queue(10)
        self.outQueue = Queue(10)


        print("in scope constructor timebase",timebase)
        try:
            print("Trying to make new thread")
            self.thread = Thread(target=runThread,args=(self.scope,self.cmdQueue,self.outQueue))
            self.thread.start()
            self.configure_timebase(timebase)
            
        except Exception as e:
            print("Unable to start thread",e)

    def configure_timebase(self,speed):
        self.cmdQueue.put(['configure_timebase',[speed]])

    def configure_channel(self,channel):
        self.cmdQueue.put(['configure_channel',[channel]])

    def close(self):
        self.cmdQueue.put(['close',[]])

    def capture_init(self):
        self.cmdQueue.put(['capture_init',[]])

    def arm(self):
        return self.capture_start()

    def capture_start(self):
        self.cmdQueue.put(['capture_start',[]])
        return self.outQueue.get()

    def get_data(self):
        self.cmdQueue.put(['get_data',[]])

        return self.outQueue.get()
      
    def channel_on(self,channelIdx,on):
        self.scope.channelOn[channelIdx] = on

    def setVoltage(self,channelIdx,voltage):
        self.scope.voltage[channelIdx] = voltage

    def setCoupling(self,channelIdx,coupling):
        self.scope.coupling[channelIdx] = coupling
   
    def setLowpass(self,channelIdx,lowpass):
        self.scope.lowpass[channelIdx] = lowpass

    def configure_trg_suf(self,val):
        self.cmdQueue.put(['trg_suf',[val]])

    def configure_trg_pre(self,val):
        self.cmdQueue.put(['trg_pre',[val]])

    def reconnect(self):
        pass

