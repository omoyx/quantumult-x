# Quantumult X：订阅与配置分开维护

通过「下载配置」保存为本地配置，再在圈 X 内添加自己的机场订阅。按地区跨机场自动测速，并为 Siri / Apple Intelligence、通用 AI、流媒体和常用服务提供独立策略。

**请选择「配置文件 → 下载配置」。把 GitHub 链接用于「新建关联」会变成只读的远程托管配置，无法添加自己的订阅。** 本地配置内引用的远程分流规则仍会独立更新。

**主配置地址：**

```text
https://raw.githubusercontent.com/omoyx/quantumult-x/main/QuantumultX.conf
```

## 第一次使用

1. 保存现有可用配置，记下 `AI` 策略当前使用的有效出口。
2. 点右下角风车，在「配置文件」区域选择「下载配置」，粘贴上面的链接并保存，使用可编辑的本地配置。该操作会覆盖当前配置，先完成上一步备份。然后在「节点 → 节点资源／引用」中添加 JMS、奶昔或其他订阅。优先使用机场的 QX 格式；其他受支持的格式可开启该资源的「资源解析」，使用模板内的 KOP-XIAO 解析器。**订阅只填在圈 X 内。**
3. 切到「分流」模式，在「其他设置」关闭「分流匹配优化」，更新节点和规则，执行一次节点延时测试。
4. 确认 `AI` 仍选原先有效的出口，并且目标地区组确实有节点，再试 Siri / Apple Intelligence。美国是新模板默认值，不代表任何特定节点一定可用。

后续添加或刷新订阅，地区组按节点名称自动纳入，无需改主配置或填写机场名。

### 已经关联 GitHub 配置，无法添加订阅

1. 保存原有可用配置；若其中已有自己的订阅，先在本机备份，记下 `AI` 的有效出口。
2. 在配置文件区域取消当前 GitHub URL 的远程关联，再选择「下载配置」，粘贴上面的同一个链接并保存。
3. 回到节点资源入口，添加自己的订阅并更新节点，检查目标地区组有候选。

本地或 iCloud 文件的关联与 GitHub URL 的远程托管不同；这里遇到的只读限制针对后者。无需把订阅发给维护者或写入 GitHub，也无需关闭圈 X 或修改系统路由。

### 日常更新

- 机场订阅独立刷新节点，地区组按名称动态纳入。
- 配置内的远程分流列表每 24 小时更新。需要时长按右下角风车，使用左侧更新按钮刷新远程资源，见[官方订阅更新说明](https://t.me/QuanXNews/21)。
- 策略组结构、地区正则和 DNS 属于本地主配置。仓库对这些内容的修改不会自动合并进本地配置；升级前保留自己的订阅和本地修改。反复「下载配置」会覆盖它们。

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

### JMS 编号节点重命名与海盗旗

先按自己的实际出口填写地区别名，在该订阅的资源路径末尾添加参数，并开启该资源的「资源解析」。以下仅演示 `c123s1` 到 `c123s5` 分别对应洛杉矶、洛杉矶、洛杉矶、大阪、荷兰时的写法；编号与地区并非所有 JMS 套餐通用。

```text
#rename=c123s1@LA-1%20洛杉矶+c123s2@LA-2%20洛杉矶+c123s3@LA-GIA%20洛杉矶+c123s4@Osaka%20大阪+c123s5@NL%20荷兰&emoji=1
```

`@` 分开旧名和新名，`+` 分开多项映射，必须保留这两个字面分隔符；空格等名称内容才编码。把分隔符写成 `%40`、`%2B` 会导致映射不生效，纯编号无法识别地区时，KOP 的 `emoji=1` 就会加上海盗旗。以上示例解析结果为三项 `🇺🇸`、一项 `🇯🇵`、一项 `🇳🇱`，分别进入美国、日本、欧洲自动组。修改后更新该节点资源即可，无需重新下载主配置。

[KOP 解析器源码](https://github.com/KOP-XIAO/QuantumultX/blob/master/Scripts/resource-parser.js)先按字面的 `+`、`@` 拆分，再解码名称字段。当前实现先重命名再添加国旗；头部关于 `rename`／`rrname` 顺序的旧说明与实现不一致，联网检查以实际解析输出为准。

## Siri 与规则更新

沿用 [Shadowrocket-Siri 的 siri3.list](https://github.com/byx020119/Shadowrocket-Siri/blob/main/siri3.list) 和 `AI` 策略。保留 32 条 QX 原生本地快照，优先于普通 Apple、Google、国内 IP 规则；同一来源的远程规则继续接收新增。该来源也覆盖 Private Relay、Maps 和指标域名，这里保留兼容行为，不宣称这些域名都是 Siri 的最小必要集合。上游删除规则时，维护者需要同步本地快照；检查程序会提示差异。

常用服务使用 blackmatrix7 的 QX 原生规则，每 24 小时更新。专用服务在前，通用服务和国内兜底在后。重写、任务、后端和 MITM 均为空；广告规则预置为关闭。

**固定链接用于首次「下载配置」到本地，主配置升级不会无损自动合并。** 节点订阅和远程分流各自更新。若重新覆盖导入主配置，先保留自己在圈 X 内添加的订阅；[QX 官方 URL Scheme](https://github.com/crossutility/Quantumult-X/blob/master/url-scheme.md)区分「添加资源」与「替换配置／资源」，二者不能混用。不要把带私人订阅的导出配置提交到本仓库。

## 验证与维护

无需安装 Python 包。离线检查：

```sh
python3 -B validate.py
```

联网复核公开源、Siri 转换、虚构 SS 节点解析、5 个虚构 JMS 编号节点的重命名和旗帜，以及典型服务分流：

```sh
python3 -B validate.py --online --report online-report.json
```

联网检查需要 Node.js；macOS 上还会用系统 Swift / Foundation 验证 ICU 正则。GitHub Actions 在每次变更和每天运行上述检查，不需要机场订阅。

本仓库检查配置结构、策略引用、57 个节点名称样例、公开资源完整性、Siri 快照以及典型域名的顺序匹配。域名模型不模拟 QX 的 DNS、ASN、HTTPS User-Agent 可见性或实际出口。用户已实测反馈 GitHub 远程关联无法添加订阅，因此使用方式已明确为下载到本地。**尚未完成本地配置添加订阅、用户节点连通性和服务解锁验收。** 确认本地导入无误、节点入组、实际请求规则与出口正确之后，才能判断特定网络的日常可用性。

## 参考来源

| 来源 | 采用内容 |
|---|---|
| [QX 官方 sample](https://github.com/crossutility/Quantumult-X/blob/master/sample.conf) | 策略语法、延时检查、force-policy 与内置规则 |
| [QX 官方 URL Scheme](https://github.com/crossutility/Quantumult-X/blob/master/url-scheme.md) | 导入与资源更新边界 |
| [QX 官方配置关联说明](https://t.me/QuanXNews/114) · [官方订阅更新说明](https://t.me/QuanXNews/21) | 远程托管、iCloud 关联与资源独立更新 |
| [fmz200 图文教程](https://github.com/fmz200/wool_scripts/blob/main/QuantumultX/How-To-Use.md) | 「下载配置」入口、覆盖提醒及随后添加节点订阅的操作 |
| [Orz-3/QuantumultX](https://github.com/Orz-3/QuantumultX) | 空订阅模板、地区与服务分组方式；其 available 策略与本配置的延时策略不同 |
| [墨鱼配置](https://ddgksf2013.top/Profile/QuantumultX.conf) | 地区正则延时策略、关闭匹配优化及专用服务顺序 |
| [blackmatrix7/ios_rule_script](https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/QuantumultX) | QX 原生服务与国内规则 |
| [KOP-XIAO/QuantumultX](https://github.com/KOP-XIAO/QuantumultX) | 在圈 X 内转换受支持的订阅和 Siri 规则 |
| [byx020119/Shadowrocket-Siri](https://github.com/byx020119/Shadowrocket-Siri) | Siri / Apple Intelligence 兼容规则 |

来源保持各自的许可与署名；本仓库没有复制社区整份配置、重写脚本或证书。公开源校验快照见 [sources.json](sources.json)。
