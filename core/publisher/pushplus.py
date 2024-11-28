import json

from tornado import httpclient

from core.publisher.publisher import BasePublisher


class PushPlusPublisher(BasePublisher):

    def __init__(self, token: str, url: str, topic: int = None):
        self._token = token
        self._url = url
        self._topic = topic

    def publish(self, content: str, title: str = None, **kwargs):
        return self._publish(data={
            "token": self._token,
            "title": title,
            "content": content,
            "topic": self._topic,  # 群组编号
            **kwargs
        })

    def _publish(self, data: dict):
        body = json.dumps(data).encode(encoding='utf-8')
        headers = {'Content-Type': 'application/json'}

        client = httpclient.HTTPClient()
        try:
            response = client.fetch(self._url, method='POST', headers=headers, body=body, validate_cert=False)
            self.logger.info("The {} published data: {} successfully".format(self.name, data))
        except httpclient.HTTPError as e:
            self.logger.error("Request failed: {}, data: {}".format(e, data))
        except Exception as e:
            self.logger.error("Request failed: {}, data: {}".format(e, data))
        finally:
            client.close()
