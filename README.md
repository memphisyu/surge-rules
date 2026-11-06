# Surge rules

将 [Hawaiine/mihomo-rules](https://github.com/Hawaiine/mihomo-rules) 转换为 Surge 远程规则。仓库只存公开规则和转换程序，不包含节点、机场订阅或个人配置。

GitHub Actions 每天北京时间 07:23 更新，也可在 Actions 页面手动运行。转换或验证失败会停止发布，请关注 Actions 的失败通知。

## 使用

主配置引用生成的规则集，例如：

```ini
[Rule]
RULE-SET,https://raw.githubusercontent.com/memphisyu/surge-rules/main/Surge/OpenAI.list,AI,update-interval=86400

[Script]
HawaiineRegex-OpenAI = type=rule,script-path=https://raw.githubusercontent.com/memphisyu/surge-rules/main/Surge/OpenAI.js,script-update-interval=86400
```

`AI` 必须替换为自己已有的策略组。完整规则引用及七个 Script 声明见 [Surge/rules.conf](Surge/rules.conf)，它只包含规则与脚本两节，不是完整客户端配置。个人网络规则和 FINAL 由主配置维护。

品牌顺序沿用上游 Nikki 模板，包含其注释中的品牌，Applications 仅提供下载、不自动加入路由。DOMAIN-REGEX 原样保存为 JavaScript RegExp，通过每品牌一个 Surge rule script 匹配 hostname；不会擅自转为 DOMAIN-SUFFIX。IP 规则添加 no-resolve。

远程文件内容自动更新；上游增加品牌，或原本没有正则的品牌新增正则时，需要更新主配置的引用或 Script 声明。manifest.json 记录上游 commit、数量和列表 SHA256。

## 本地验证

需要 Python 3.12+、Node.js 22+：

```sh
python -m venv .venv
.venv/bin/pip install -r requirements.txt
git clone --depth 1 https://github.com/Hawaiine/mihomo-rules.git upstream
.venv/bin/python -m unittest -v
.venv/bin/python convert.py --upstream upstream --output Surge --base-url https://raw.githubusercontent.com/memphisyu/surge-rules/main/Surge --revision "$(git -C upstream rev-parse HEAD)"
node verify.js Surge
```

Node 验证不代表 Surge 实际联网验收。上游许可证与来源说明保存在 Surge/LICENSE 和 Surge/NOTICE。
