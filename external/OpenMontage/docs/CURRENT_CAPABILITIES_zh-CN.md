# OpenMontage 当前能力清单（本机实况）

本文档描述的是 **当前这台机器、当前这套环境变量、当前这份仓库** 的真实能力，不是 README 里的理想能力。

适用路径：

- 项目根目录：`D:\桌面文件下载\AI-hermes-agent\external\OpenMontage`
- 上层环境变量来源：`D:\桌面文件下载\AI-hermes-agent\.env`
- 环境加载脚本：`D:\桌面文件下载\AI-hermes-agent\scripts\openmontage_env.ps1`

---

## 1. 当前项目是什么

OpenMontage 现在可以作为一个 **视频生产中台 / 视频 Agent 底层执行层** 来使用。

它当前的核心能力是：

1. 接收一个视频任务
2. 选择合适的 pipeline
3. 生成脚本、分镜、场景计划、视频提示词
4. 调用不同 provider 生成真实视频镜头或图像/语音/音乐素材
5. 把结果保存到 `projects/<project-name>/...`

它已经很适合做：

- TikTok/抖音带货视频前期生产
- 商品广告视频脚本和镜头设计
- 参考视频拆解
- 真运动镜头生成
- 多 provider 视频生成路由

---

## 2. 当前已具备的主要能力

### 2.1 视频任务规划能力

项目已经具备完整的 pipeline 生产结构：

- `research`
- `proposal`
- `script`
- `scene_plan`
- `assets`
- `edit`
- `compose`

这意味着它不只是“生成一个 prompt”，而是能按生产阶段拆任务。

### 2.2 当前已有的 pipeline

当前仓库里存在这些 pipeline：

- `animated-explainer`
- `animation`
- `avatar-spokesperson`
- `character-animation`
- `cinematic`
- `clip-factory`
- `documentary-montage`
- `hybrid`
- `localization-dub`
- `podcast-repurpose`
- `screen-demo`
- `talking-head`

### 2.3 当前可用的视频生成能力

本机当前已确认 `available` 的视频生成入口：

- `video_selector`
- `kling_video`
- `seedance_video`
- `veo_video`
- `siliconflow_video`
- `pixverse_video`
- `vidu_video`
- `ark_video`

这些能力意味着：

- 已可走 `fal.ai` 路线生成真运动视频
- 已可直连 `SiliconFlow`
- 已可直连 `PixVerse`
- 已可直连 `Vidu`
- 已可直连 `Ark`

### 2.4 当前可用的图像 / 语音 / 音乐能力

当前已确认 `available`：

- `google_imagen`
- `google_tts`
- `pixabay_music`

当前已确认 `unavailable`：

- `doubao_tts`

### 2.5 参考视频拆解能力

项目支持：

- 读取 YouTube / 本地视频 / 短视频作为参考
- 分析 pacing、structure、style、scene pattern
- 输出 grounded summary 和新的视频方向建议

这部分依赖 `AGENT_GUIDE.md` 里的 `Reference Video Entry Point` 流程。

---

## 3. 每个能力怎么调用

### 3.1 最基础的调用方式

先进入上层项目目录，加载环境变量：

```powershell
cd "D:\桌面文件下载\AI-hermes-agent"
. .\scripts\openmontage_env.ps1
```

再进入 OpenMontage：

```powershell
cd "D:\桌面文件下载\AI-hermes-agent\external\OpenMontage"
```

### 3.2 作为 Codex 调用

Codex 的标准调用方式：

1. 打开 OpenMontage 根目录
2. 先读：
   - `AGENT_GUIDE.md`
   - `PROJECT_CONTEXT.md`
   - `CODEX.md`
3. 确定 pipeline
4. 生成或读取：
   - `brief`
   - `script`
   - `scene_plan`
   - `provider prompts`
5. 调用具体工具生成资产

如果是商品带货视频，通常最适合从 `cinematic` 或 `hybrid` pipeline 开始。

### 3.3 作为 Hermes 调用

Hermes 更适合做“任务入口”和“业务层编排”：

1. Hermes 先生成商品卡 / Product Opportunity Card
2. 再生成视频任务 brief
3. 再把 job 交给 Codex / OpenMontage 执行
4. 收回输出路径、日志和成片状态

适合的职责划分：

- Hermes：业务决策、商品结构化、任务下发
- OpenMontage：视频生产执行
- Codex：作为执行代理驱动 OpenMontage pipeline

### 3.4 直接调用视频生成工具

如果你不想先走完整 pipeline，也可以直接通过 Python 调工具。

示例思路：

```python
from tools.tool_registry import registry
registry.ensure_discovered()
tool = registry.get("video_selector")
result = tool.execute({
    "prompt": "...",
    "preferred_provider": "kling",
    "operation": "text_to_video",
    "aspect_ratio": "9:16",
    "duration": "5",
    "output_path": "projects/demo/assets/video/sample.mp4",
})
print(result.success, result.data)
```

可直接点名的 provider：

- `preferred_provider="kling"`
- `preferred_provider="seedance"`
- `preferred_provider="veo"`

如果你想绕开 selector，也可以直接调单个工具，例如：

- `kling_video`
- `siliconflow_video`
- `pixverse_video`
- `vidu_video`
- `ark_video`

### 3.5 当前新增 provider 的直接调用方向

#### `siliconflow_video`

适合：

- 使用 `SILICONFLOW_API_KEY`
- 直连 SiliconFlow Wan 视频模型

当前支持：

- `text_to_video`

#### `pixverse_video`

适合：

- 使用 `PIXVERSE_API_KEY`
- 直连 PixVerse 生成视频

当前支持：

- `text_to_video`
- `image_to_video`

#### `vidu_video`

适合：

- 使用 `VIDU_API_KEY`
- 直连 Vidu 生成视频

当前支持：

- `text_to_video`
- `image_to_video`

#### `ark_video`

适合：

- 使用 `ARK_API_KEY`
- 直连 Ark 视频任务接口

当前支持：

- `text_to_video`
- `image_to_video`

可通过 `ARK_BASE_URL` 覆盖站点地址。

---

## 4. 当前哪些已经打通

### 4.1 已经打通的环境共享

OpenMontage 已经可以继承上层项目环境变量。

当前确认共享成功的关键变量能力包括：

- `FAL_KEY`
- `SILICONFLOW_API_KEY`
- `PIXVERSE_API_KEY`
- `VIDU_API_KEY`
- `ARK_API_KEY`
- `GEMINI_API_KEY`
- `GOOGLE_API_KEY`（如果存在）

### 4.2 已经打通的真实视频链路

已经明确打通过的链路：

- `OpenMontage -> 上层 .env -> FAL_KEY -> fal.ai -> Kling`

并且已经成功生成过真实样片：

- `projects/drone-tiktok-ad-v3/assets/video/sample_takeoff_kling_retry.mp4`

这说明：

- 当前不是只能做 PPT/静态图动画
- 已经能真正生成运动镜头

### 4.3 已经打通的 provider 适配

已完成适配并被 registry 识别：

- `siliconflow_video`
- `pixverse_video`
- `vidu_video`
- `ark_video`

### 4.4 已经打通的任务设计能力

你现在已经可以让它：

- 根据产品图生成带货脚本
- 生成 `brief.md`
- 生成 `scene_plan.md`
- 生成 provider prompts
- 输出 sample clip

---

## 5. 当前哪些还差一步

### 5.1 自动成片闭环还没完全打通

当前最关键的未完成点：

- `video_compose` 当前状态为 `unavailable`

这意味着：

- 生成镜头素材：可以
- 自动把素材、字幕、音乐、旁白一次性合成最终交付成片：当前还没完全闭环

### 5.2 Doubao TTS 还没打通

当前状态：

- `doubao_tts = unavailable`

所以豆包语音现在还不能直接用，需要继续排查：

- `DOUBAO_SPEECH_API_KEY` 是否正确加载
- 接口区站 / 认证格式是否匹配

### 5.3 还有一些 key 虽然已共享，但未完全接线

目前仍属于“环境已共享，但项目还没完整落地能力”的包括：

- `RUNNINGHUB_API_KEY`
- `LIBLIB_ACCESS_KEY`
- `LIBLIB_SECRET_KEY`
- `KLING_API_KEY`

说明：

- `KLING_API_KEY` 目前没有做官方直连适配
- 当前 Kling 主要还是走 `FAL_KEY`
- `RUNNINGHUB` 更像 workflow gateway，适配复杂度高于普通视频 API
- `LIBLIB` 可以做，但还需要更稳的接口确认和实现

### 5.4 不是所有 provider 都已经“实战生成验证”

当前虽然这些工具已经 `available`：

- `siliconflow_video`
- `pixverse_video`
- `vidu_video`
- `ark_video`

但目前做过明确成功样片验证的，是：

- `kling_video`（通过 fal）

所以其余新 provider 目前属于：

- 已接线
- 已被发现
- 已能读取环境变量
- 但还建议先逐个跑 sample 验证

---

## 6. 当前最适合你的使用方式

结合你现在的目标，推荐这样用：

### 方案 A：带货视频生产

1. 用商品图生成 brief
2. 生成英文脚本
3. 生成分镜
4. 先用 `kling` 或 `seedance` 跑关键镜头 sample
5. 样片满意后批量生成镜头
6. 再解决 compose 闭环

### 方案 B：多 provider 压测

如果你要比较效果，可以对同一个镜头分别跑：

- `kling_video`
- `siliconflow_video`
- `vidu_video`
- `ark_video`
- `pixverse_video`

然后比较：

- 动作真实感
- 提示词服从度
- 价格
- 出片稳定性

### 方案 C：Hermes + Codex + OpenMontage

推荐结构：

- Hermes：生成商品卡 / brief / 任务下发
- Codex：读 OpenMontage 规则并执行
- OpenMontage：作为视频生产工具层

---

## 7. 一句话总结

当前这套 OpenMontage，已经具备：

- 真实视频镜头生成能力
- 多 provider 视频路由能力
- 商品广告脚本与分镜生产能力
- 参考视频拆解能力
- 上层 `.env` 共享调用能力

但目前还没有完全具备：

- 稳定的一键自动最终成片闭环

所以它现在最准确的定位是：

**“已经能跑真运动镜头和视频生产前期流程的底层视频 Agent 系统，但自动交付最终成片还差 compose 这最后一步。”**
