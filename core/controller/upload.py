import logging
from io import BytesIO

from tornado.web import RequestHandler

from core.reader import EnzeReader

UploadMaxSize = 5 * 1024 * 1024


class UploadHandler(RequestHandler):
    def get(self):
        self.render("upload.html")

    def post(self):
        """文件更新"""
        files = self.request.files["file"]
        for file in files:
            filename = file.filename
            allowed_types = [
                "application/vnd.ms-excel",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ]
            if file["content_type"] not in allowed_types:
                return self.write(f"文件 '{filename}' 不是有效的 Excel 文件")

            body = file["body"]
            if len(body) > UploadMaxSize:
                return self.write(f"文件 '{filename}' 大小不允许超过 5MB")

            stream_body = BytesIO(body)
            if (reader := self.application.settings.get(EnzeReader.name)) and reader.handle(stream_body):
                self.write(f"文件 '{filename}' 已上传成功")
            else:
                return self.write(f"服务异常")
