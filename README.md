# Quantumult X：订阅与配置分开维护

导入一次，在圈 X 内添加自己的机场订阅。按地区跨机场自动测速，并为 Siri / Apple Intelligence、通用 AI、流媒体和常用服务提供独立策略。

**主配置地址：**

```text
https://raw.githubusercontent.com/omoyx/quantumult-x/main/QuantumultX.conf
```

## 第一次使用

1. 保存现有可用配置，记下 `AI` 策略当前使用的有效出口。
2. 在 Quantumult X 中从上面的链接下载／导入配置。再在「节点资源／引用」中添加 JMS、奶昔或其他订阅。优先使用机场的 QX 格式；其他受支持的格式可开启该资源的「资源解析」，使用模板内的 KOP-XIAO 解析器。**订阅只填在圈 X 内。**
3. 切到「分流」模式，在「其他设置」关闭「分流匹配优化」，更新节点和规则，执行一次节点延时测试。
4. 确认 `AI` 仍选原先有效的出口，并且目标地区组确实有节点，再试 Siri / Apple Intelligence。美国是新模板默认值，不代表任何特定节点一定可用。

后续添加或刷新订阅，地区组按节点名称自动纳入，无需改主配置或填写机场名。

## 策略

| 策略 | 默认行为 |
|---|---|
| 美国、日本、台湾、香港、新加坡、欧洲、韩国、加拿大、澳大利亚自动 | 跨订阅筛选同地区节点，选择较低延时的节点 |
| 全球自动 | 所有正常命名节点；常见流量、到期和通知条目除外 |
| 默认代理 | 全球自动；可手动改选某地区或节点 |
| AI | Siri / Apple Intelligence 专用；默认美国自动 |
| AI服务 | OpenAI、Claude、Gemini、AI Studio、NotebookLM、Copilot、Perplexity；默认美国自动 |
| 流媒体 | 通用国际媒体；默认全球自动 |
| Netflix、Disney+、YouTube、Spotify、巴哈姆特 | 单独选区；巴哈姆特默认台湾自动 |
| Apple、Microsoft | 默认直连；专用 AI 和流媒体规则优先 |
| Google、Telegram | 默认代理，可独立选地区 |
| 手动节点 | 所有正常命名节点，可固定一个出口 |
| 兜底 | 默认代理；国内域名和 CN IP 在此前直连 |

自动组使用 `url-latency-benchmark`，活跃时每 600 秒检测，延时改善达到约 50 ms 才换节点，空闲时不持续检测。延时测试不验证带宽、实际国家、AI 或流媒体解锁；自动切换可能更换出口 IP。

测速参数采用 `server_check_url = http://cp.cloudflare.com/generate_204`。该参数保持 HTTP，以兼容会拒绝 HTTPS 检测网址的 QX 版本；配置下载地址和远程规则仍使用 HTTPS。如果旧版本在第 11 行提示 `malformed server check URL`，将测速这一行的 `https://` 改成 `http://`。网址在浏览器中能访问，不代表圈 X 的配置解析器接受它。

名称支持中英文地名、城市、缩写和旗帜，例如 `🇯🇵 Tokyo`、`HK-01`、`JMS Los Angeles`。纯编号 `c123s4`、`JMS-01` 无法可靠推断国家，会保留在全球自动和手动节点；这类节点可在圈 X 内加真实地区别名。中转与落地同时出现在名称中可能匹配多个地区。订阅重名节点可加机场前缀区分，但不要给一个多地区订阅统一加国家前缀。

没有节点的地区组会为空，没有跨地区回退；当前 QX 的空组行为未实机核验，不能把空组当成阻断保证。首次使用先检查所选组有候选。

## Siri 与规则更新

沿用 [Shadowrocket-Siri 的 siri3.list](https://github.com/byx020119/Shadowrocket-Siri/blob/main/siri3.list) 和 `AI` 策略。保留 32 条 QX 原生本地快照，优先于普通 Apple、Google、国内 IP 规则；同一来源的远程规则继续接收新增。该来源也覆盖 Private Relay、Maps 和指标域名，这里保留兼容行为，不宣称这些域名都是 Siri 的最小必要集合。上游删除规则时，维护者需要同步本地快照；检查程序会提示差异。

常用服务使用 blackmatrix7 的 QX 原生规则，每 24 小时更新。专用服务在前，通用服务和国内兜底在后。重写、任务、后端和 MITM 均为空；广告规则预置为关闭。

**固定链接用于导入，不承诺主配置升级无损合并。** 节点订阅和远程分流各自更新。若重新覆盖导入主配置，先保留自己在圈 X 内添加的订阅；QX 官方区分「添加资源」与「替换配置／资源」，二者不能混用。不要把带私人订阅的导出配置提交到本仓库。

## 验证与维护

无需安装 Python 包。离线检查：

```sh
python3 -B validate.py
```

联网复核公开源、Siri 转换、虚构 SS 节点解析和典型服务分流：

```sh
python3 -B validate.py --online --report online-report.json
```

联网检查需要 Node.js；macOS 上还会用系统 Swift / Foundation 验证 ICU 正则。GitHub Actions 在每次变更和每天运行上述检查，不需要机场订阅。

本仓库检查配置结构、策略引用、57 个节点名称样例、公开资源完整性、Siri 快照以及典型域名的顺序匹配。域名模型不模拟 QX 的 DNS、ASN、HTTPS User-Agent 可见性或实际出口。**尚未完成 QX 实机导入、用户节点连通性和服务解锁验收。** 本机记录中确认导入无误、节点入组、实际请求规则与出口正确之后，才能判断特定网络的日常可用性。

## 参考来源

| 来源 | 采用内容 |
|---|---|
| [QX 官方 sample](https://github.com/crossutility/Quantumult-X/blob/master/sample.conf) | 策略语法、延时检查、force-policy 与内置规则 |
| [QX 官方 URL Scheme](https://github.com/crossutility/Quantumult-X/blob/master/url-scheme.md) | 导入与资源更新边界 |
| [Orz-3/QuantumultX](https://github.com/Orz-3/QuantumultX) | 空订阅模板、地区与服务分组方式；其 available 策略与本配置的延时策略不同 |
| [墨鱼配置](https://ddgksf2013.top/Profile/QuantumultX.conf) | 地区正则延时策略、关闭匹配优化及专用服务顺序 |
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/QuantumultX) | QX 原生服务与国内规则 |
| [KOP-XIAO/QuantumultX](https://github.com/KOP-XIAO/QuantumultX) | 在圈 X 内转换受支持的订阅和 Siri 规则 |
| [byx020119/Shadowrocket-Siri](https://github.com/byx020119/Shadowrocket-Siri) | Siri / Apple Intelligence 兼容规则 |

来源保持各自的许可与署名；本仓库没有复制社区整份配置、重写脚本或证书。公开源校验快照见 [sources.json](sources.json)。
