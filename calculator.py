#!/usr/bin/env python3

import sys
from multiprocessing import Queue,Process,Lock
from datetime import datetime
import getopt
import configparser

class Config(object):
    def __init__(self,filename,arg='DEFAULT'):
        self._filename = filename
        self._arg = arg
        self._obj = configparser.ConfigParser(strict=False)
        self._obj.read(self._filename)
    
    @property
    def basel(self):
        return self._obj.getfloat(self._arg,'JiShuL')
    
    @property
    def baseh(self):
        return self._obj.getfloat(self._arg,'JiShuH')
  
    @property
    def soinsurp(self):
        sum = 0
        for i in ['YangLao','GongJiJin','ShengYu','GongShang','ShiYe','YiLiao']:
            sum += self._obj.getfloat(self._arg,i)
        return sum

class UserData(object):
    def __init__(self,userdatafile):
        self._userdatafile = userdatafile
   
    @property 
    def userdata(self):
        userdata = {}
        with open(self._userdatafile) as file:
            for line in file:
                s = line.split(',')
                fkey = s[0].strip()
                fvalue = s[1].strip()
                userdata[fkey] = float(fvalue)
        return userdata
    
      

class Salary(object):
    #bftax is salary before the pitax
    #soinsurp is socail insur pecentage
    #basel is the lowest base
    #baseh is the hightest base
    def __init__(self,bftax,soinsurp,basel,baseh):
        self._bftax = bftax
        self._soinsurp = soinsurp
        self._basel = basel
        self._baseh = baseh

    @property 
    def soinsur(self):
        if self._bftax <= self._basel:
            return self._basel * self._soinsurp
        elif self._bftax >= self._baseh:
            return self._baseh * self._soinsurp
        else:
            return self._bftax * self._soinsurp
    
    @property
    def pitax(self):
        taxbase = self._bftax - self.soinsur - 3500
        if taxbase <= 0:
            return 0
        elif taxbase > 0 and taxbase <= 1500:
            return taxbase * 0.03
        elif taxbase > 1500 and taxbase <= 4500:
            return (taxbase * 0.1 - 105)
        elif taxbase > 4500 and taxbase <= 9000:
            return (taxbase * 0.2 - 555)
        elif taxbase > 9000 and taxbase <= 35000:
            return (taxbase * 0.25 - 1005)
        elif taxbase > 35000 and taxbase <= 55000:
            return (taxbase * 0.3 - 2755)
        elif taxbase > 55000 and taxbase <= 80000:
            return (taxbase * 0.35 - 5505)
        else:
            return (taxbase * 0.45 - 13505)
    @property
    def aftax(self):
        return self._bftax - self.soinsur - self.pitax                          
 
que1 = Queue()
que2 = Queue()

def putda_func(arg,lock):
    #
    user_inst = UserData(arg)
    g = [ (k,v) for k,v in\
     user_inst.userdata.items()]
    for i in g:
        with lock:
            que1.put(i)

def comp_func(soinsurp,basel,baseh,lock):
        while True:
            i = que1.get()
            bftax = i[1]
            salary = Salary(bftax,soinsurp,basel,baseh)
            sal_list = [i[0],i[1],salary.soinsur,salary.pitax,\
                     salary.aftax]
            with lock:
                que2.put(sal_list)
            if que1.empty():
                break


def outfi_func(arg):
    while True:
        lis = que2.get()       
        with open(arg,'a') as file:
            file.write(lis[0])
            for i in lis[1:]:
                file.write(','+'{:.2f}'.format(i))
            t = datetime.now()
            t_str = datetime.strftime(t,'%Y-%m-%d %H:%M:%S')
            file.write(',' + t_str)
            file.write('\n')
        if que2.empty():
            break 

def usage():
    line1= '-h --help print the man of the pargamer'
    line2= '-C cityname -c configfile -d userdatafile -o outputfile'
    print(line1)
    print(line2)


def main():
    try:
        opts,args = getopt.getopt(sys.argv[1:],'c:o:d:C:h',['--help',])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)
   
    cityname = 'DEFAULT'   
    userfile = None
    configfile = None
    outfile = None

    for o,a in opts:
        if o in ("-h","--help"):
            usage()
            sys.exit()
        try:
            if o == '-o':
                 outfile = a
            elif o == '-C':
                 cityname = a
            elif o == '-d':
                 userfile = a
            elif o == '-c':
                 configfile = a 
            else:         
                 raise ParatermeterError
        except:
            usage()
            print("Paramter Error")
            sys.exit(2)
    try:
        config = Config(configfile,cityname)
        lo1 = Lock()
        lo2 = Lock()
        Process(target=putda_func,args=(userfile,lo1)).start()
        Process(target=comp_func, args=(config.soinsurp,\
        config.basel,config.baseh,lo2)).start()
        Process(target=outfi_func, args=(outfile,)).start()
    except:
        print("Paramter Error")
            
if __name__ == '__main__': 
    main()
