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
