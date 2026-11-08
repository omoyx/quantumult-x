# Quantumult X：订阅与配置分开维护

本地主配置维护节点、地区策略与 DNS；远程分流维护网站该走哪个策略。已有配置只需添加下面的自定义分流，之后随远程资源更新，不再整份替换配置。

## 已有配置只添加分流

[一键添加自定义分流](https://quantumult.app/x/open-app/add-resource?remote-resource=%7B%22filter_remote%22%3A%5B%22https%3A%2F%2Fraw.githubusercontent.com%2Fomoyx%2Fquantumult-x%2Fmain%2Frules%2FCustom.list%2C%20tag%3D%E8%87%AA%E5%AE%9A%E4%B9%89%E5%88%86%E6%B5%81%2C%20update-interval%3D86400%2C%20opt-parser%3Dfalse%2C%20inserted-resource%3Dtrue%2C%20enabled%3Dtrue%22%5D%7D)

该链接使用 QX 官方 `add-resource`，只增加一条 `filter_remote`，保留已有订阅和配置。若没有唤起圈 X，可复制以下地址到「分流 → 引用／远程资源」新增：

```text
https://raw.githubusercontent.com/omoyx/quantumult-x/main/rules/Custom.list
```

首次添加后核对这三项：

1. 将「自定义分流」放到远程分流首位，开启「插入资源」，关闭该资源的「资源解析」。
2. **保留文件内的策略，不为整个资源指定统一策略。** 此列表混合使用 `direct`、`AI`、`AI服务`，适配本仓库此前的主配置；如果使用其他配置，应先确认存在 `AI`、`AI服务` 这两个同名策略。
3. 使用「分流」模式，关闭「其他设置 → 分流匹配优化」，刷新该资源。自动更新间隔为 86400 秒；可手动刷新以立即接收修复。

若偏好编辑本地配置，只在 `[filter_remote]` 最上方添加这一行即可，其他段落保留：

```ini
https://raw.githubusercontent.com/omoyx/quantumult-x/main/rules/Custom.list, tag=自定义分流, update-interval=86400, opt-parser=false, inserted-resource=true, enabled=true
```

### 本次内容传输调整

- App Store 的 `iosapps` 下载端点、`icloud-content.com`／`.com.cn` 内容传输直接走 `direct`。
- `content-storage-upload.googleapis.com` 这一窄存储域名族走 `direct`，避免被 Google 通配规则送进代理；其他 Google API 保持原策略。它有 CloudKit 资产上传的公开实测旁证，仍需验证使用地的直连可达性。
- `gateway.icloud.com` 共享 CloudKit 网关走 `direct`。其余既有 Siri／PCC 兼容域名继续走 `AI`，通用 AI 补充走 `AI服务`。
- 不新增 Apple 整个 IP 网段的直连覆盖，不将所有 `icloud.com` 或第三方云存储整体直连。私人 NAS 域名仅在自己的本地分流里设为 `direct`，不要写入本公开仓库，也不要直连整个公共 DDNS 后缀。

`inserted-resource=true` 使这份规则先于旧本地 Siri 快照生效，因此旧的 `gateway.icloud.com → AI` 无需手动删除。新主配置不再复制自定义域名的本地快照。已有配置的旧规则可作为停用本资源后的回退；今后取消旧域名策略时，维护者必须发布明确覆盖，不能仅从远程列表删掉旧条目。

**Siri 实机验收与回退：** 更新后试一次原来可用的 Siri／Apple Intelligence 请求，同时确认内容上传正常。本仓库检查不能证明设备功能和直连链路已经通过。若共享网关直连后出现功能回退，可直接编辑此资源 URL，把 `Custom.list` 改为 `Custom-compat.list` 并刷新；兼容版仅将共享网关恢复到 `AI`，其他内容直连不变。也可先停用原资源，再[添加兼容版](https://quantumult.app/x/open-app/add-resource?remote-resource=%7B%22filter_remote%22%3A%5B%22https%3A%2F%2Fraw.githubusercontent.com%2Fomoyx%2Fquantumult-x%2Fmain%2Frules%2FCustom-compat.list%2C%20tag%3D%E8%87%AA%E5%AE%9A%E4%B9%89%E5%88%86%E6%B5%81%2C%20update-interval%3D86400%2C%20opt-parser%3Dfalse%2C%20inserted-resource%3Dtrue%2C%20enabled%3Dtrue%22%5D%7D)，两版不要同时启用。

以后调整网站分流只更新此列表，机场订阅继续自行更新；地区策略结构、图标与 DNS 的改动仍属于本地主配置。远程分流不能替你创建新策略组。

## 全新安装的主配置

已有用户无需再次导入这个文件。只有第一次建立完整策略和地区组时，才通过「配置文件 → 下载配置」保存为本地配置，随后自行添加机场订阅。GitHub URL 的「新建关联」属于只读远程托管，无法在其中添加自己的订阅。

```text
https://raw.githubusercontent.com/omoyx/quantumult-x/main/QuantumultX.conf
```

## 第一次使用

1. 保存现有可用配置，记下 `AI` 策略当前使用的有效出口。
2. 点右下角风车，在「配置文件」区域选择「下载配置」，粘贴上面的 `QuantumultX.conf` 链接并保存，使用可编辑的本地配置。该操作会覆盖当前配置，先完成上一步备份。然后在「节点 → 节点资源／引用」中添加 JMS、奶昔或其他订阅。优先使用机场的 QX 格式；其他受支持的格式可开启该资源的「资源解析」，使用模板内的 KOP-XIAO 解析器。**订阅只填在圈 X 内。**
3. 切到「分流」模式，在「其他设置」关闭「分流匹配优化」，更新节点和规则，执行一次节点延时测试。
4. 确认 `AI` 仍选原先有效的出口，并且目标地区组确实有节点，再试 Siri / Apple Intelligence。美国是新模板默认值，不代表任何特定节点一定可用。

后续添加或刷新订阅，地区组按节点名称自动纳入，无需改主配置或填写机场名。

### 策略图标与已有配置更新

全部 25 个自定义策略指定图标：地区用旗帜、欧洲用地图，品牌服务用标志。`AI` 使用 [离歌图标库](https://github.com/lige47/lige_icon) 的 Apple Intelligence 图形，Disney+ 使用青绿色版本，Google 使用渐变 G；这三张固定引用已检查的上游提交 `e28d76f`，避免上游替换同名图片影响本配置。Apple 改用简洁灰色标志，其余沿用 [Koolson / Qure Color](https://github.com/Koolson/Qure)。图标由原项目远程提供并保留来源署名。

品牌样式参考 [Disney+ 2024 品牌更新](https://press.disneyplus.com/about/disney-plus-logo-2024)和 [Google 渐变 G 官方说明](https://blog.google/company-news/inside-google/company-announcements/gradient-g-logo-design/)。

已经加过私人订阅时，在本地配置编辑器中，仅用本仓库配置的 `[policy]` 段替换对应段：从 `[policy]` 复制到下一个 `[server_remote]` 之前，保留本机 `[server_remote]` 及其他段落。不要为换图标整份覆盖配置。若自己改过策略内容，只给同名策略行追加相应的 `img-url=...`。圈 X 内各策略当前选中的出口仍需核对，特别是原先有效的 `AI` 出口。

图标链接使用 QX 官方支持的 `img-url`，在线检查会核验图片响应、PNG 格式及尺寸；图片可用不代表已完成用户设备上的显示验收。策略名称、候选、地区正则和测速参数与换图标前一致。

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

### JMS 短名称，国旗放在最前

在 JMS 节点资源中开启「资源解析」，用下面的片段**替换资源路径原有的整个 `#...` 部分**，然后更新该资源。保留 `#` 前的私人订阅原样，不需要重新下载主配置。

以下用虚构编号 `c123` 演示：按已知的五节点映射，`s1`／`s2`／`s3` 是洛杉矶、`s4` 是大阪、`s5` 是荷兰。使用时将五处 `c123` 换成自己节点显示的编号；这是指定映射，不会查询实际出口，也不代表所有 JMS 套餐通用。

```text
#replace=(%2C%5Cs*tag=)[^%2C]*%5Cbc123s1%5Cb[^%2C]*@$1🇺🇸%20洛杉矶①+(%2C%5Cs*tag=)[^%2C]*%5Cbc123s2%5Cb[^%2C]*@$1🇺🇸%20洛杉矶②+(%2C%5Cs*tag=)[^%2C]*%5Cbc123s3%5Cb[^%2C]*@$1🇺🇸%20洛杉矶③+(%2C%5Cs*tag=)[^%2C]*%5Cbc123s4%5Cb[^%2C]*@$1🇯🇵%20大阪+(%2C%5Cs*tag=)[^%2C]*%5Cbc123s5%5Cb[^%2C]*@$1🇳🇱%20荷兰
```

更新后的完整名称：

```text
🇺🇸 洛杉矶①
🇺🇸 洛杉矶②
🇺🇸 洛杉矶③
🇯🇵 大阪
🇳🇱 荷兰
```

它们分别进入美国、日本、欧洲自动组。保留三个洛杉矶编号以便区分节点，移除重复的中英文地名、个人编号、域名、协议和倍率；这里不额外标注未经核实的线路名称。

旧 `rename=c123s1@新名称` 只替换名称中的这一小段，原有前后缀会保留，国旗就可能留在中间。现在改用 [KOP 解析器](https://github.com/KOP-XIAO/QuantumultX/blob/master/Scripts/resource-parser.js)的 `replace` 替换整个 `tag` 值；表达式限定在逗号分隔的名称字段内，保留连接参数，且 `s1` 不会匹配 `s10`。直接写入国旗，不需要叠加旧 `rename`、`emoji` 或 `delreg` 参数。其他编号保持原名。

`@` 和 `+` 是解析器的字面分隔符，不能整体编码成 `%40`／`%2B`；`%2C`、`%5C`、`%20` 分别是表达式中的逗号、反斜线和名称空格，`$1` 保留名称字段开头。公开解析器已用虚构节点验证前后缀清理、国旗首位、未匹配节点及连接字段不变；这不能替代设备上的实际显示和节点连通性验收。

#### s801：按用途标为下载

[JMS 官方目录](https://www.justmysocks.net/members/index.php?rp=/knowledgebase/1/General)将 `s801` 列为 Freedom server，说明可用流量取决于当前倍率。[详细条目](https://www.justmysocks.net/members/index.php?rp=/knowledgebase/13/What-is-Freedom-server-s801.html)在 2026-11-08 的未登录访问中要求登录，因此这里不声称核实了当前账户倍率、出口国家或质量／在线率条款。若后台显示 Freedom ×10，按十倍可用流量理解，实际下载 20 GB 对应约 2 GB 套餐用量；这是条件示例，不是当前倍率或速度承诺。

可把下面这一段直接接到上面 `#replace=...` 的最末尾，同样将 `c123` 换成自己的节点编号。不要再加一个 `#replace=`：

```text
+(%2C%5Cs*tag=)[^%2C]*%5Cbc123s801%5Cb[^%2C]*@$1📥%20下载
```

完整名称会变为 `📥 下载`。它不写死倍率或国家，也不会仅靠名称进入美国自动组；**当前仍会进入全球自动和手动节点**。改名不会使流量自动专用于下载，也不会把节点排除出全球自动。下载时可以手选，实际速度需测试；日常 AI／Siri 建议沿用已验证的出口。

## Siri 与规则更新

在自定义远程列表中维护 [Shadowrocket-Siri 的 siri3.list](https://github.com/byx020119/Shadowrocket-Siri/blob/main/siri3.list) 的兼容域名：共享网关单独直连，其余 31 条保留 `AI`，优先于普通 Apple、Google 和国内 IP 规则。该来源也覆盖 Private Relay、Maps 和指标域名，不宣称这些都是 Siri 的最小必要集合。上游增删会使检查失败，维护者审阅后再发布；不将未经审阅的社区修改直接覆盖到用户设备。兼容版仅让共享网关恢复 `AI`。

常用服务使用 blackmatrix7 的 QX 原生规则，每 24 小时更新。专用服务在前，通用服务和国内兜底在后。重写、任务、后端和 MITM 均为空；广告规则预置为关闭。

**`rules/Custom.list` 是日常规则订阅；`QuantumultX.conf` 只用于首次建立本地配置，主配置升级不会无损自动合并。** 节点订阅和远程分流各自更新。若重新覆盖导入主配置，先保留自己在圈 X 内添加的订阅；[QX 官方 URL Scheme](https://github.com/crossutility/Quantumult-X/blob/master/url-scheme.md)区分「添加资源」与「替换配置／资源」，二者不能混用。不要把带私人订阅的导出配置提交到本仓库。

## 验证与维护

无需安装 Python 包。离线检查：

```sh
python3 -B validate.py
```

联网复核公开源、25 个策略图标的 PNG 与尺寸、Siri 转换、虚构 SS 节点解析、JMS 编号节点重命名及完整短名替换、连接字段保持，以及典型服务分流：

```sh
python3 -B validate.py --online --report online-report.json
```

发布后可用 `python3 -B validate.py --online --published --report online-report.json` 同时核对两份在线自定义规则与规范源一致。通常的 `--online` 使用工作区中的自定义列表，以支持发布前和 PR 检查。

联网检查需要 Node.js；macOS 上还会用系统 Swift / Foundation 验证 ICU 正则。GitHub Actions 在每次变更和每天运行上述检查，不需要机场订阅。

本仓库检查配置结构、策略引用、63 个节点名称样例、公开资源完整性、Siri 兼容域名、内容直连、旧本地规则覆盖和一键添加链接，以及典型域名的顺序匹配。域名模型不模拟 QX 的 DNS、ASN、HTTPS User-Agent 可见性或实际出口。用户已实测反馈 GitHub 远程关联无法添加订阅，因此使用方式已明确为下载到本地。**尚未完成本地配置添加订阅、用户节点连通性和服务解锁验收。** 确认本地导入无误、节点入组、实际请求规则与出口正确之后，才能判断特定网络的日常可用性。

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
| [Koolson / Qure](https://github.com/Koolson/Qure) | Qure Color 策略图标，远程引用并保留来源署名 |
| [lige47 / lige_icon](https://github.com/lige47/lige_icon) | Apple Intelligence、青绿色 Disney+、渐变 Google G；远程引用固定提交并注明出处 |
| [byx020119/Shadowrocket-Siri](https://github.com/byx020119/Shadowrocket-Siri) | Siri / Apple Intelligence 兼容规则 |

来源保持各自的许可与署名；本仓库没有复制社区整份配置、重写脚本或证书。内容端点参考 [Apple 网络要求](https://support.apple.com/en-us/101555)及 [CloudKit 上传实测](https://developer.apple.com/forums/thread/822534)。公开源校验快照见 [sources.json](sources.json)。
