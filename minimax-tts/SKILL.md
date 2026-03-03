---
name: minimax-tts
description: 使用 MiniMax API 将文本转换为语音并自动播放。当用户需要将文字转成语音、朗读文本、生成音频时使用。触发词：文字转语音、TTS、生成语音、朗读、minimax tts、语音合成。
---

# MiniMax TTS

生成语音后**自动播放**（macOS 用 `afplay`）。凭据从 `~/.vk-cowork/.env` 读取。

## 用法

```bash
# 生成并直接播放（不保存文件）
python3 ~/.claude/skills/minimax-tts/scripts/tts.py "要朗读的文本"

# 生成、播放并保存
python3 ~/.claude/skills/minimax-tts/scripts/tts.py "文本" output.mp3

# 只保存不播放
python3 ~/.claude/skills/minimax-tts/scripts/tts.py "文本" output.mp3 --no-play

# 带情绪
python3 ~/.claude/skills/minimax-tts/scripts/tts.py "文本" --emotion happy --speed 1.2
```

## 参数

| 参数 | 说明 | 默认 |
|------|------|------|
| `text` | 文本（必填） | — |
| `output` | 保存路径（可选，省略则用临时文件播放后删除） | — |
| `--voice` | 音色 ID | `MINIMAX_TTS_VOICE_ID` 环境变量 |
| `--speed` | 语速 0.5–2.0 | `1.0` |
| `--emotion` | 情绪 | — |
| `--model` | 模型 | `speech-02-hd` |
| `--no-play` | 只保存，不播放 | — |

## 常用音色

`Chinese (Mandarin)_Soft_Girl`（默认）/ `male-qn-qingse` / `female-shaonv` / `presenter_male` / `audiobook_female_1`

## 情绪

`happy` / `sad` / `angry` / `fearful` / `disgusted` / `surprised` / `neutral`（仅 `speech-02-*` 模型）

## 语气词标签（仅 speech-2.8-hd / speech-2.8-turbo）

直接嵌入文本中，例如：`"(inhale)好的，(emm)让我想想。(sighs)"`

| 标签 | 效果 | 标签 | 效果 |
|------|------|------|------|
| `(laughs)` | 笑声 | `(chuckle)` | 轻笑 |
| `(sighs)` | 叹气 | `(breath)` | 换气 |
| `(inhale)` | 吸气 | `(exhale)` | 呼气 |
| `(pant)` | 喘气 | `(gasps)` | 倒吸气 |
| `(emm)` | 嗯 | `(humming)` | 哼唱 |
| `(coughs)` | 咳嗽 | `(clear-throat)` | 清嗓子 |
| `(groans)` | 呻吟 | `(sniffs)` | 吸鼻子 |
| `(snorts)` | 喷鼻息 | `(burps)` | 打嗝 |
| `(lip-smacking)` | 咂嘴 | `(hissing)` | 嘶嘶声 |
| `(sneezes)` | 喷嚏 | | |
