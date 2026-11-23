# v7 规格与 20 条素材表 — Sunday 22 November 2026

> 核心策略：**更少的字、更大的图、更多的留白**。在 v6（98.60%，第 158 名）基础上，将故事从 26 条进一步精选为 **20 条（15 张 3×5 大卡 + 5 条单行带图标简讯）**，全面改用无边框暖报纸开放排布与纯平涂剪影海报插画（零细线噪点），顶部 KPI 精简为 4 格 56px 超大数字，全幅 8 条 128px 横带边缘密度全部压至 ≤35。
> 纯 Python + Pillow 确定性绘制，1024×1024 原生像素，≤1,048,576 字节，两次运行 MD5 完全一致。

## 1. 版式架构（1024×1024 原生像素，区块间距 12px，无厚外框开放排布）

| 区域 | Y 区间 | 高度 | 规格说明 |
|---|---|---|---|
| 1. 顶部深蓝细条 | `0..16` | 16px | 全宽深海军蓝 `#101D3D`，左 `THE WORLD IN ONE DAY`（金色），右 `20 STORIES · 7 REGIONS · SUNDAY 22 NOVEMBER 2026`（白色） |
| 2. 超大红字日期报头 | `18..62` | 44px | `Sunday 22 November 2026`（54px 猩红粗衬线 `#9E1F28` 居中占满宽度）+ `65` 单道细猩红饰线 |
| 3. 4 格超大数字条 | `68..134` | 66px | 无外框开放 4 等宽格（细竖分割线），**56px** 深海军蓝粗衬线共享基线数字 + **11px** 清晰说明标签；全部由 `STORIES` 正则提取校验 |
| 4. 7 色区域条 | `138..154` | 16px | 7 区实色比例分段，内嵌 `区域名 + 计数`（动态统计，每区 2–3 条，合计 20 条） |
| 5. DAY IN UTC 时间轴 | `158..176` | 18px | 深蓝单行带 `#162647`，左标 `DAY IN UTC`，右 **8 个等宽关键 UTC 时刻**（金色时刻 + 白色短摘要，零折行） |
| *(呼吸留白)* | `176..188` | 12px | 统一 12px 区块间距 |
| 6A. 首行 3 张旗舰主卡（#1–#3，3 列） | `188..406` | 218px | 无外框直落暖报纸底色 `#F8F3E9`，列宽 324px、列距 12px；顶部全宽 **`324×150px` 平涂海报大插画**（高度 **150px**，占卡高 **68.8%**），下方 20px 粗衬线标题 + 13px 导语 + 9px 来源 |
| *(呼吸留白)* | `406..418` | 12px | 统一 12px 区块间距 + 极淡水平分栏线 |
| 6B. 第 2–5 行 12 张大卡（#4–#15，3 列 × 4 行） | `418..824` | 406px | 每行高 `94px`，行距 `10px`，列宽 `324px`、列距 `12px`；左侧 **`150×92px` 平涂海报插画**（宽度 150px、占卡高 **97.9%**），右侧 `164px` 留白排布 18–20px 粗衬线标题（≤2 行）+ 12–13px 导语（≤2 行）+ 9px 来源 |
| *(呼吸留白)* | `824..836` | 12px | 统一 12px 区块间距 |
| 7. 下半部：左地图 + 右 5 条简讯 | `836..952` | 116px | 左 `x=14..314` 为 **`300×116px`** 极简世界地图（标示全球 7 区 **10 枚**关键故事编号钉）；右 `x=326..1010` 为 **5 条单行简讯**（#16–#20），每条左侧 `18×18px` 双色调实心图标 + 单行标题、地点与来源 |
| *(呼吸留白)* | `952..964` | 12px | 统一 12px 区块间距 |
| 8. 底部留白区（DATE CHECK + 单行页脚） | `964..1024` | 60px | `964..992`（28px）`DATE CHECK — READ THIS FIRST` 声明（≤2 行，左侧 3px 猩红竖线，无厚边框）+ `992..1010` **18px 纯白呼吸留白** + `1010..1022` 单行页脚 |

> **1024×1024 纵向物理约束说明**：首行 3 张旗舰主卡插画严格达到 `324×150px`（高 **150px**，占卡高 68.8%），第 2–5 行 12 张 3 列卡插画为 `150×92px`（宽 **150px**，占卡高 97.9%）；在严格 3×5（5 行）+ 56px KPI + 地图 + 5 条简讯 + 底部留白的 1024px 画布上实现最大画面占比与 300px 旗舰层次。

## 2. 顶部 4 格大数字条（56px，全部由 20 条素材正则提取核验）

| 数值 | 标签 | 对应故事 | 核验依据（2026-11-22 当日） |
|---|---|---|---|
| `186` | Drones fired at Ukraine | #2 | 俄军 11 月 22 日夜间向乌克兰发射 186 架无人机 |
| `161` | Drones downed | #2 | 乌方防空与电子战击落或压制 161 架 |
| `$120bn` | COP31 finance floor | #1 | COP31 谈判破裂核心分歧：1200 亿美元/年适应资金下限被删 |
| `74,742` | Gaza death toll | #12 | 加沙卫生部门 11 月 22 日更新累计死亡人数 |

## 3. DAY IN UTC 时间轴（8 个单行关键时刻）

1. `01:00` — HK polls open (#5)
2. `01:25` — Cartel seized (#7)
3. `03:00` — COP31 fails (#1)
4. `04:00` — Vegas F1 GP (#15)
5. `09:20` — Korea ed. quit (#17)
6. `10:44` — Mercury orbit (#6)
7. `14:05` — Banten fire (#9)
8. `20:43` — Alcaraz ATP (#11)

## 4. 7 区域均衡分布（总计 20 条，每区 2–3 条）

| 区域 | 条数 | 15 大卡（3×5） | 5 条简讯 |
|---|---|---|---|
| EUROPE | 3 | #2, #10, #11 | — |
| ASIA-PACIFIC | 3 | #5, #9 | #17 |
| AMERICAS | 3 | #7, #13, #15 | — |
| MIDDLE EAST | 3 | #4, #12 | #16 |
| AFRICA | 3 | #3, #14 | #18 |
| OCEANIA | 2 | #8 | #19 |
| WORLD | 3 | #1, #6 | #20 |
| **合计** | **20** | **15 张大卡** | **5 条简讯** |

## 5. 精选 20 条 2026-11-22 真实国际新闻素材表

### 15 张大卡区（#1–#15，3 列 × 5 行，全部配备 2–3 色调平涂海报插画）

| # | 区域 | 领域 | 标题 | 导语 | 来源媒体 | 插画主题（平涂 2–3 色调） |
|---|---|---|---|---|---|---|
| 1 | WORLD | CLIMATE | COP31 collapses in Antalya | Nearly 200 nations deadlock past 03:00 UTC over fossil fuels and a $120bn floor. | Reuters, AFP, BBC | 深青会场底、裂纹象牙地球与金色木槌 |
| 2 | EUROPE | MILITARY | Russia fires 186 drones; 161 downed | Overnight wave of 72 jet UAVs batters Dymer flats and triggers grid blackouts. | Ukr. Air Force, BBC | 午夜基辅天际线、双探照光束与金色三角翼拦截火光 |
| 3 | AFRICA | MILITARY | Warship Merkury sinks in Benghazi | Russian corvette capsizes after suspected sea-drone strike off Libya. | Reuters, Al Jazeera | 暮海双色底、倾覆战舰剪影与红金火羽 |
| 4 | MIDDLE EAST | MILITARY | Iran strike hurts 2 in Bahrain | Manama cites Sitra fire; IRGC claims Patriot hit. | MEE, Times of Israel | 暮暗底、象牙炼油罐红金烈焰与雷达盘 |
| 5 | ASIA-PACIFIC | POLITICS | HK polls hit 98.8% with 856 | Election body fills 723 seats as 5,640 vote. | info.gov.hk, China Daily | 蓝灰底、象牙投票箱、白选票与猩红大勾 |
| 6 | WORLD | SPACE | BepiColombo reaches Mercury | Probe enters orbit after 8 yrs to map crust. | BBC, ESA | 深空底、暖砂陨坑水星与双翼金轨探测器 |
| 7 | AMERICAS | SECURITY | Mexico seizes cartel chief | Forces nab FBI Most Wanted boss Meza Flores. | BBC, Reuters | 靛夜底、山峦剪影、白色直升机与金色光锥 |
| 8 | OCEANIA | SPORT | India hits record 720/9 | Visitors set NZ Test mark before hosts draw. | ESPN, Jamaica Obs. | 绿茵底、三柱门、木球棒与猩红板球弧线 |
| 9 | ASIA-PACIFIC | DISASTER | Banten plant fire kills 3 | Rescuers comb gutted factory; 36 missing. | AFP, BBC | 炭夜底、锯齿厂房亮窗与三层烈焰浓烟 |
| 10 | EUROPE | POLITICS | Fico blocks €45bn EU loan | Slovak PM vetoes EU aid package for Ukraine. | Reuters, Kyiv Post | 欧盟深蓝底、12 金星、白欧元与红否决杠 |
| 11 | EUROPE | SPORT | Alcaraz wins ATP Finals | Spaniard tops Zverev in Turin for first title. | Reuters, Guardian | 室内蓝球场底、金色双耳冠军杯与黄绿网球 |
| 12 | MIDDLE EAST | CRISIS | Gaza toll hits 74,742 | Health ministry updates toll; talks urged. | WAFA, Anadolu | 暮色霞光层叠底、深黑剪影天际线与淡月 |
| 13 | AMERICAS | SPORT | Wembanyama drops 50 pts | Spurs star posts 50-pt, 19-reb Texas night. | CBS, KSAT | 炭黑球馆底、白篮板橙篮筐与巨幅橙篮球 |
| 14 | AFRICA | CONFLICT | Drones strike Khartoum | RSF UAVs hit homes and UN site; four killed. | Al Jazeera | 暮紫底、深色屋顶天际线、爆燃红光与白机影 |
| 15 | AMERICAS | SPORT | Verstappen wins Vegas F1 | Beats both McLarens under Las Vegas lights. | Guardian, BBC | 霓虹夜赛道底、F1 赛车剪影与黑白格子旗 |

### 5 条补充简讯区（#16–#20，单行排布 + 18×18px 实心双色图标）

| # | 区域 | 标题 | 地点与导语 | 来源媒体 | 图标主题 |
|---|---|---|---|---|---|
| 16 | MIDDLE EAST | Lebanon marks 83rd Independence Day | Beirut · Displaced locals return for holiday | NPR, L'Orient | 雪松树实心剪影 |
| 17 | ASIA-PACIFIC | S. Korea education chief quits | Seoul · Resigns over AI exam chaos | AFP, BBC | 试卷与金色芯片 |
| 18 | AFRICA | Boat capsize kills 24 mourners | Bayelsa, Nigeria · River tragedy strikes | AllAfrica | 倾斜船影与青浪 |
| 19 | OCEANIA | Pope urges aid for PNG drought | Port Moresby · All 22 zones hit by drought | Crux, CathNews | 金阳与水滴剪影 |
| 20 | WORLD | WTO flags $1.5tn & $5.4tn curbs | Geneva · Record global trade barriers | WTO, SunStar | 集装箱与红禁杠 |

## 6. 世界地图 10 个关键锚点（覆盖全部 7 区域）

`#1` Antalya · `#2` Kyiv · `#3` Benghazi · `#4` Sitra (Bahrain) · `#5` Hong Kong · `#7` Sinaloa · `#8` Wellington · `#9` Banten · `#15` Las Vegas · `#18` Bayelsa (Nigeria)

## 7. DATE CHECK 主动剔除清单（2 行内）

- **Peru M6.7 quake**（20 Nov）
- **Russia 400-drone barrage**（19–20 Nov；11 月 22 日实为 186 架）
- **APEC Shenzhen summit**（19 Nov）
- **French Senate vote**（20 Nov）
