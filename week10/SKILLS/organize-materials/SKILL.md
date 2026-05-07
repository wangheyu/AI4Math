---
name: organize-materials
description: |
  Incrementally organize math study materials from 原始素材/ into structured folders
  (实变函数, 数学分析, 其他). Extracts archives, classifies by subject and content type,
  deduplicates, and merges new files into the existing organized structure.
  Trigger when the user says "organize materials", "整理素材", "更新材料", "sync materials",
  or mentions new files in 原始素材.
---

# Organize Math Study Materials

This skill incrementally processes the `原始素材/` directory, extracting new archives
and organizing their contents into the structured folder hierarchy.

## How it works

1. Scans `原始素材/` for new or changed files (tracked via `.claude/manifest.json`)
2. Extracts any new ZIP/RAR archives to a temp directory
3. Classifies extracted files by subject (实变函数, 数学分析, 其他) and content type
   (textbooks, lectures, notes, exercises, exams, homework, review_guides, references)
4. Checks MD5 hash against all existing organized files to skip duplicates
5. Copies new unique files into the appropriate organized folders
6. Updates the manifest so the same files aren't processed again

## Usage

Run the organizer script:

```bash
python3 .claude/scripts/organize_materials.py
```

## Directory structure

```
原始素材/                  Source materials (archives + standalone PDFs)
实变函数/                  Real Analysis — organized
数学分析/                  Mathematical Analysis — organized
其他/数据结构基础_FDS/      FDS — organized
.claude/
├── manifest.json          Tracks processed source files
├── scripts/
│   └── organize_materials.py
└── skills/
    └── organize-materials.md
```

## Content categories

| Category | Description |
|---|---|
| textbooks | Full textbook PDFs and solution guides |
| lectures | Course slides, schedules, supplementary notes from instructors |
| notes | Student notes, theorem compilations, mind maps |
| exercises | Problem sets, exercise class materials, textbook exercise solutions |
| exams/final | Final exam papers |
| exams/midterm | Midterm exam papers |
| exams/quizzes | Short quizzes |
| exams/course_N | Exams organized by course number (数学分析 I/II/III) |
| homework | Weekly homework and answer keys |
| review_guides | Review outlines, exam prep materials |
| references | External reference books and exam papers from other universities |

## Notes

- The script is idempotent — safe to run multiple times
- Uses `bsdtar` for extraction (handles both ZIP and RAR)
- All content is in Chinese; classification uses both Chinese and English keywords
- Original source files in `原始素材/` are never modified
