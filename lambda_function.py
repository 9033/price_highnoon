import time
import json

import threading

import urllib.parse
import urllib.request
import urllib.error

def requestGET(url,param,header=None): #urllib 버전. 
  p = urllib.parse.urlencode(param)
  if header==None:
    req = urllib.request.Request(url=url+'?'+p) # using get method
  else:
    req = urllib.request.Request(url=url+'?'+p, headers=header) # using get method

  try:
    res = urllib.request.urlopen(req)
    return {'status' : res.getcode(), 'text' : res.read() }
  except urllib.error.HTTPError as err:
    # HTTP 에러도 동일한 인터페이스로 반환해서 재시도 여부를 상위에서 판단하게 한다.
    return {'status' : err.code, 'text' : err.read() }
  except Exception:
    # 네트워크 예외는 수집 실패로 간주하고 해당 항목을 생략하기 위해 None을 반환한다.
    return None


def reqGET(url,param,header=None):#interface 통일.
  for _ in range(4):
    res=requestGET(url,param,header)
    if res and res['status']==200:#ok
      return res
    time.sleep(1)

  return None

rets={}
rets_lock=threading.Lock()

def setrets(key,stringify, value): #리턴값을 전역 변수에 저장. threading이라서 리턴값을 전역변수를 통해 읽음.
  global rets
  # 여러 스레드가 동시에 결과를 기록해도 같은 dict를 안전하게 갱신한다.
  with rets_lock:
    rets[key]={
      'stringify':stringify,
      'value':value,
    }

def fromupbit():
  url='https://api.upbit.com/v1/ticker'
  p={'markets':'KRW-BTC'}   
  res=reqGET(url,p)

  if not res:
    return

  try:
    jsonRes=json.loads(res['text'])
    value = int(jsonRes[0]['trade_price'])
    setrets('upbit','{:,}'.format(value), value)
  except (ValueError, KeyError, IndexError, TypeError):
    # 응답 포맷이 예상과 다르면 해당 거래소 값만 생략한다.
    return

def frombitmex():
  h={  'content-type' : 'application/json',
    'Accept': 'application/json'} 
  p={'symbol':'XBTUSD','depth':'1'}   
  url='https://www.bitmex.com/api/v1/orderBook/L2'
  res=reqGET(url,p,h)

  if not res:
    return

  try:
    jsonRes=json.loads(res['text'])
    value = float(jsonRes[0]['price'])
    setrets('bitmex','{:,.2f}'.format(value), value)
  except (ValueError, KeyError, IndexError, TypeError):
    return

def fromBinance():
  limit=10
  p={'symbol':'BTCUSDT','limit':limit}
  url='https://api.binance.com/api/v3/trades'
  res=reqGET(url,p)

  if not res:
    return

  try:
    jsonRes=json.loads(res['text'])
    avgTradePrice = sum([float(trade['price']) for trade in jsonRes]) / limit
    setrets('binance','{:,.2f}'.format(avgTradePrice), avgTradePrice)
  except (ValueError, KeyError, IndexError, TypeError, ZeroDivisionError):
    return

def getKRWUSD():
  url='https://quotation-api-cdn.dunamu.com/v1/forex/recent'
  p={'codes':'FRX.KRWUSD'}
  res=reqGET(url,p)

  if not res:
    return

  try:
    jsonRes=json.loads(res['text'])
    value = float(jsonRes[0]['basePrice'])
    setrets('hanabank',None, value)
  except (ValueError, KeyError, IndexError, TypeError):
    return

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

  # Lambda warm start에서도 이전 호출 결과가 섞이지 않도록 시작할 때마다 비운다.
  rets = {}
  
  t=threading.Thread(target=fromupbit)
  # t2=threading.Thread(target=frombitmex)
  t3=threading.Thread(target=fromBinance)
  # t4=threading.Thread(target=getKRWUSD)
  t.start()
  # t2.start()
  t3.start()
  # t4.start()
  t.join()
  # t2.join()
  t3.join()
  # t4.join()

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
