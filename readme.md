# 오후12시 비트코인 시세
## 개요
다른 투자 대상도 마찬가지지만 비트코인의 시세도 매 시간마다 변동하는데요  
그렇지만 여러 이유로 매 시간마다 시세를 보지 않는 경우에 유용할 거 같아서  
보통 점심시간이 시작하는 오후 12시(KRT)에 대표적인 거래소 사이트인  
업비트와 Binance의 비트코인 시세를 알려주는 채널을 개설 했습니다.  

![](price_highnoon.png)

**https://t.me/price_highnoon**

위에 있는 링크를 클릭하면 해당 채널로 들어갈 수 있습니다.

1비트 코인의 값을 보여줄때 단위는  
업비트는 원(BTC/KRW) Binance는 달러(BTC/USD)입니다.

하루에 한번 시세는 다음과 같이 Binance와 업비트에서 받아서  
telegram에 개설된 해당 채널로 보내게 됩니다.  

```mermaid
sequenceDiagram
	par
		price_highnoon->>Binance API: BTC/USD 요청
		Binance API->>price_highnoon: BTC/USD
	and
		price_highnoon->>두나무 하나은행 API: 원달러 환율 요청
		두나무 하나은행 API->>price_highnoon: 원달러 환율
	and
		price_highnoon->>업비트 API: BTC/KRW 요청
		업비트 API->>price_highnoon: BTC/KRW
	end
	Note over price_highnoon: 김프 구하기
	price_highnoon->>텔레그램 API: 김프, BTC/KRW, BTC/USD 전송
	Note over 텔레그램 API: price_highnoon 채널에 출력
```

## 파일
[lambda_function.py](lambda_function.py) : aws lambda에 올라가는 코드  

## 참고
### REST API를 이용한 업비트 시세 수신  
https://docs.upbit.com/docs/upbit-quotation-restful-api

### bitmex 호가 수신  
https://www.bitmex.com/api/explorer/#!/OrderBook/OrderBook_getL2

### binance 거래가격 API  
https://binance-docs.github.io/apidocs/spot/en/#recent-trades-list

### aws lambda에 layer를 추가해서 requests모듈 사용  
https://github.com/mthenw/awesome-layers  
-> https://github.com/keithrozario/Klayers  
-> https://github.com/keithrozario/Klayers/blob/master/arns/ap-northeast-2.json  

## 로그
### 2019-11-12
단순이 get호출이여서 requests대신 빌트인된 urllib를 사용하여 라이브러리 의존도를 줄임.  
물론 수행시간은 주로 api을 호출하고 대기하는 시간이 대부분이라서 큰 차이가 없다.  

```py
def requestGET(url,param,header=None): #requests 버전.
    if header==None:
        res=requests.get(url,params = param)    
    else:
        res=requests.get(url,params = param, headers = header)    
    return {'status' : res.status_code, 'text' : res.text }
```

### 2020-3-23
powershell에서 zip으로 압축한후에 aws cli를 이용해서 함수를 업데이트. [update.ps1](update.ps1)  

### 2021-5-24
바이넨스에서 비트코인의 값을 가지고 옴.
하나은행의 환율 정보로 김프를 계산해서 출력.

## 새로 만든 채널 혹은 채팅방의 id를 아는 방법.
채널이나 채팅방을 만들고 봇을 초대한다.  
새로 만든 곳에서 아무 메세지나 입력한다.  
getUpdate로 새로 업데이트된 메시지를 받는다.  
아까 입력한 메시지에 있는 id가 새로 만든 채널 혹은 채팅방의 id임.  
