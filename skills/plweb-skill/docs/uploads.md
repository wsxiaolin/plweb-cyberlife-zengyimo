# 图片上传

本地使用 `CommunityActions.set_avatar(image_path)` 与 `set_cover(summary_id,image_path,category="Experiment")`。ChatGPT插件使用 `upload_avatar`、`upload_cover`，必填 `image_source`：`base64` 时只填原始 `image_base64` 字符串（不含data:前缀）；`plugin_file` 时只填 `image_file_id`。

`image_file_id` 只能是本插件 `store_file_chunk` 返回的 `plfile_…`，文件必须 `kind=image` 且 `complete=true`。ChatGPT附件ID、生成图片的附件ID和路径都不能直接传入。先在有文件读取能力的环境中读取附件字节，分块Base64保存到本插件，再使用返回ID。

例如 `upload_avatar({image_source:"plugin_file",image_file_id:"plfile_<UUID>"})`。小图也可 `upload_avatar({image_source:"base64",image_base64:"<原始Base64>"})`。两种方式均可选传 `account_id`。封面工具另外必填 `summary_id`，可选 `category`。

## 头像

1. 读取当前用户最新Avatar，使用新序号Avatar+1。
2. 调用RequestAvatar，Request为`{Extension:".jpg",FileSize:-图片字节数}`。
3. 用返回的Data凭据上传，核对实际目标并读取最终图片；只有完整有效、非空白且符合目标的图片才继续确认。
4. ConfirmAvatar传`{Avatar:新序号}`，重新GetUser核对。

头像文件上限为 **1,048,576字节（1MiB）**；封面文件上限为 **8,388,608字节（8MiB）**，发送前拒绝超限文件。图片格式为 JPEG、PNG 或 WebP。像素尺寸与文件字节数是两个不同概念；插件不另设宽高像素上限，不能将文件大小写成1024×1024像素。

## 封面

1. GetSummary读取当前摘要；保持Image原值，使用原Summary和Request=`{Extension:".jpg",FileSize:-图片字节数}`申请上传凭据。不要先递增Image，也不要先调用ConfirmExperiment。
2. 从凭据的policy.save-key（Upyun）或RequestURI（OSS对象key）取得实际目标路径和序号，核对属于当前作品；存储响应中的url必须与目标一致。
3. 上传后先验证实际目标图片可访问、完整且不是空白图，再按实际目标序号调用ConfirmExperiment，Extension=".jpg"，最后重新GetSummary。目标图片校验失败时保留原封面，不确认新序号。
4. GET摘要指向的实际图片地址，要求HTTP200且数据确为图片。只有摘要序号、上传目标和图片可访问性全部一致，才返回updated=true / coverUploaded=true；仅序号一致不能宣称成功。

推荐封面 **800×600（4:3）**。当前服务端策略包含 `/both/800x600/quality/90/`，非4:3图片会居中裁剪；文字、边框应留安全边距。默认简化预览也使用800×600。

对象路径固定为 `/experiments/images/{摘要ID前4位}/{第5至6位}/{第7至8位}/{余下ID}/{序号}.jpg`。`.jpg`是服务端对象名，内容可能仍是PNG，实际格式以Content-Type和文件头为准；不要改探`.png`或`.jpg.png`。ConfirmExperiment.Extension与申请上传时使用的`.jpg`一致。网页的 `!block` 等后缀是独立的图片处理样式，不是扩展名。

实测图片CDN返回 `Cache-Control: max-age=691200`（8天）。正常替换封面使用新索引，避免覆盖旧路径造成缓存陈旧；不为修复索引而重复上传一份图片，也不默认旧对象会被清理。

## 存储上传表单

- RequestHost非空：向该HTTPS地址发送key=RequestURI、OSSAccessKeyId=AccessKey、policy=Policy、Signature=Authorization及file。
- RequestHost为空：向`https://v0.api.upyun.com`加RequestURI发送authorization、policy及file。
- file使用image.jpg文件名，实际图片支持JPEG、PNG或WebP。上传程序内部处理临时凭据；不向图片主机发送账号Token/AuthCode。

`publish`默认根据模型生成封面，也可指定图片。命令行示例：

```text
python scripts/community_cli.py --account <用户ID> avatar --image <图片>
python scripts/community_cli.py --account <用户ID> cover --summary-id <摘要ID> --image <图片>
```

## 完整性与存储响应

Base64必须由原文件字节程序化生成，不能让模型手工复制、拼接或删减长编码。分块仅切割原始字节，再分别编码每块；不要任意切开Base64后分别解码。即使少了4个字符，长度仍可能是4的倍数，格式检查无法证明完整。上传前核对原文件字节数/哈希；辅助代码还检查PNG分块CRC与结束块、JPEG结束标记和WebP声明长度，损坏时在申请上传凭据前报错。

上传HTTP成功仍需检查JSON业务code与url。Upyun可能返回 `code=200` 同时带 `message="invalid app name: no name"`；此消息保留在storageMessage中，不单凭它判定文件上传失败，也不能忽略后续校验。辅助流程核对实际url、确认索引并验证CDN图片；这些成功才报告成功。

头像与封面上传前应查看目标原图，不能用1×1占位图或临时测试图代替用户图片。云端可传image_bytes、image_sha256核对原图；分块完成会返回bytes和sha256。辅助代码默认阻止可识别的纯色/全透明PNG（含本次白图），仅用户明确要求纯色图时才用allow_blank_image=true；这不是对任意JPEG/WebP图像内容的视觉识别，上传者仍须核对图片内容。

直接通过通用写入工具确认头像/封面序号或修改摘要Image时，同样会检查实际图片；缺失、损坏或已识别为空白的图片不能通过直接改序号绕过。清除自定义图片的0序号保留。
