import json
import urllib.request
from config import CF_ACCOUNT_ID,CF_TOKEN,CF_MODEL

class CloudflareProvider:

    def chat(self,prompt):

        url=f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{CF_MODEL}"

        data=json.dumps({

            "messages":[

                {

                    "role":"user",

                    "content":prompt

                }

            ]

        }).encode()

        req=urllib.request.Request(

            url,

            data=data,

            headers={

                "Authorization":"Bearer "+CF_TOKEN,

                "Content-Type":"application/json"

            }

        )

        try:

            with urllib.request.urlopen(req,timeout=120) as r:

                result=json.loads(r.read().decode())

            if "result" in result:

                if "response" in result["result"]:

                    return result["result"]["response"]

                return str(result["result"])

            return str(result)

        except Exception as e:

            return "Cloudflare Error: "+str(e)
