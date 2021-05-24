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

def setrets(key,stringify, value): #리턴값을 전역 변수에 저장. threading이라서 리턴값을 전역변수를 통해 읽음.
    global rets
    cond=threading.Condition()
    cond.acquire()
    rets[key]={
      'stringify':stringify,
      'value':value,
    }
    cond.release()

def fromupbit():
    url='https://api.upbit.com/v1/ticker'
    p={'markets':'KRW-BTC'}   
    res=reqGET(url,p)

    if res['status']==200:
        jsonRes=json.loads(res['text'])
        value = int(jsonRes[0]['trade_price'])
        setrets('upbit','{:,}'.format(value), value)
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
        value = float(jsonRes[0]['price'])
        setrets('bitmex','{:,.2f}'.format(value), value)
    else:
        setrets('bitmex','get price error from bitmex')

def fromBinance():
    p={'symbol':'BTCUSDT','limit':'10'}
    url='https://api.binance.com/api/v3/trades'
    res=reqGET(url,p)

    if res['status']==200:
        jsonRes=json.loads(res['text'])
        avgTradePrice = sum([float(trade['price']) for trade in jsonRes]) / 10
        setrets('binance','{:,.2f}'.format(avgTradePrice), avgTradePrice)
    else:
        setrets('binance','get price error from binance')

def getKRWUSD():
    url='https://quotation-api-cdn.dunamu.com/v1/forex/recent'
    p={'codes':'FRX.KRWUSD'}
    res=reqGET(url,p)

    if res['status']==200:
        jsonRes=json.loads(res['text'])
        value = float(jsonRes[0]['basePrice'])
        setrets('hanabank',None, value)
    else:
        setrets('hanabank','get price error from hanabank')

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
    t3=threading.Thread(target=fromBinance)
    t4=threading.Thread(target=getKRWUSD)
    t.start()
    t3.start()
    t4.start()
    t.join()
    t3.join()
    t4.join()
    
    # 김프 구하기 (#1)
    try:
      KPremium = (rets['upbit']['value'] / (rets['binance']['value'] * rets['hanabank']['value'])) - 1
      rets['K-premium']={
        'stringify':'{:,.1f}%'.format(KPremium * 100),
        'value':KPremium,
      }
    except:
      pass

    sss=[]
    for k in rets:#결과를 합침.
      if rets[k]['stringify']:
        sss.append(k+' : '+(rets[k]['stringify']))
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