import time
import json

import threading

import urllib.parse
import urllib.request

def requestGET(url,param,header=None): #urllib 버전. 
    p = urllib.parse.urlencode( param )
    if header==None:
        req = urllib.request.Request(url=url+'?'+p) # using get method
    else:
        req = urllib.request.Request(url=url+'?'+p, headers=header) # using get method
    res = urllib.request.urlopen(req)
    return {'status' : res.getcode(), 'text' : res.read() }


def reqGET(url,param,header=None):#interface 통일.
    for _ in range(4):
        res=requestGET(url,param,header)
        if res['status']==200:#ok
            break
        time.sleep(1)

    return res

rets={}

def setrets(key,val): #리턴값을 전역 변수에 저장. threading이라서 리턴값을 전역변수를 통해 읽음.
    global rets
    cond=threading.Condition()
    cond.acquire()
    rets[key]=val
    cond.release()

def fromupbit():
    url='https://api.upbit.com/v1/ticker'
    p={'markets':'KRW-BTC'}   
    res=reqGET(url,p)

    if res['status']==200:
        jsonRes=json.loads(res['text'])    
        setrets('upbit','{:,}'.format(int(jsonRes[0]['trade_price'])))
    else:
        setrets('upbit','get price error from upbit')

def frombitmex():
    h={  'content-type' : 'application/json',
      'Accept': 'application/json'} 
    p={'symbol':'XBTUSD','depth':'1'}   
    url='https://www.bitmex.com/api/v1/orderBook/L2'
    res=reqGET(url,p,h)

    if res['status']==200:
        jsonRes=json.loads(res['text'])
        setrets('bitmex','{:,.2f}'.format(float(jsonRes[0]['price'])))
    else:
        setrets('bitmex','get price error from bitmex')

def sendtoMBIN(msg):
    infojson = open("info.json","tr")
    info = json.load(infojson)
    infojson.close()

    sendmsgurl='https://api.telegram.org/'+info['botinfo']+'/SendMessage'
    param={}
    param['chat_id']=info['chat_id'] # price_highnoon 채널
    param['text']=msg
    
    req=reqGET(sendmsgurl,param)

    if req['status']==200:
        return True
    else:
        return False
        
def lambda_handler(event, context):
    global rets
    
    t=threading.Thread(target=fromupbit)
    t2=threading.Thread(target=frombitmex)
    t.start()
    t2.start()
    t.join()
    t2.join()
    
    sss=[]
    for k in rets:#결과를 합침.
        sss.append(k+' : '+(rets[k]))
    priceMsg="\n".join(sss)
    if 'test' not in event:#'test'가 활성화 되면 결과를 텔레그램에 보내지 않음.
        sendtoMBIN(priceMsg)
    return {
        'statusCode': 200,
        'body': json.dumps(priceMsg)
    }

if __name__=='__main__':#텔레그램대신 화면에 출력.
    r=lambda_handler({'test':True},None)
    print(r)