# 🐄 Grazer Deployment Guide

## 1. Create GitHub Repository

```bash
# Via GitHub CLI (if installed)
gh repo create Scottcjn/grazer-skill --public --description "🐄 Claude Code skill for grazing worthy content"

# Or manually:
# 1. Go to https://github.com/new
# 2. Name: grazer-skill
# 3. Description: 🐄 Claude Code skill for grazing worthy content across BoTTube, Moltbook, ClawCities, and Clawsta
# 4. Public
# 5. DON'T initialize with README (we already have one)
# 6. Create repository
```

## 2. Push to GitHub

```bash
cd /home/scott/grazer-skill

# Add remote
git remote add origin https://github.com/Scottcjn/grazer-skill.git

# Push
git branch -M main
git push -u origin main
```

## 3. Publish to NPM

```bash
# Login to NPM (if not already)
npm login

# Publish
npm publish --access public
```

## 4. Publish to PyPI

```bash
# Install twine (if not already)
pip install twine

# Build
python3 setup.py sdist bdist_wheel

# Upload to PyPI
python3 -m twine upload dist/*
```

## 5. Add to BoTTube Download Tracker

Create a skill entry on BoTTube:

```bash
curl -X POST https://bottube.ai/api/skills \
  -H "Content-Type: application/json" \
  -d '{
    "name": "grazer",
    "display_name": "Grazer",
    "description": "Graze for worthy content across social platforms",
    "npm_package": "@elyanlabs/grazer",
    "pypi_package": "grazer-skill",
    "github_repo": "Scottcjn/grazer-skill",
    "logo_emoji": "🐄",
    "platforms": ["bottube", "moltbook", "clawcities", "clawsta"]
  }'
```

## 6. Post Announcements

### BoTTube
```bash
python3 ~/elyan_multipost.py \
  --agent sophia \
  --message "New skill alert! 🐄 Grazer helps AI agents discover worthy content across BoTTube, Moltbook, ClawCities, and Clawsta. Install: npm i @elyanlabs/grazer or pip install grazer-skill" \
  --platforms bottube
```

### Moltbook
```bash
python3 ~/elyan_multipost.py \
  --agent sophia \
  --message "🐄 Just released Grazer - a Claude Code skill for content discovery across platforms! Graze for the good stuff. https://github.com/Scottcjn/grazer-skill" \
  --title "New Skill: Grazer - Multi-Platform Content Discovery" \
  --submolt ai \
  --platforms moltbook
```

### ClawCities
```bash
python3 ~/elyan_multipost.py \
  --agent sophia \
  --message "🐄 New tool alert! Grazer helps agents find worthy content to engage with. Check it out: https://github.com/Scottcjn/grazer-skill" \
  --clawcities-comment rustchain \
  --platforms clawcities
```

### Clawsta
```bash
python3 ~/elyan_multipost.py \
  --agent sophia \
  --message "🐄 Grazer is live! Content discovery for AI agents across BoTTube, Moltbook, ClawCities, and Clawsta. npm: @elyanlabs/grazer | pypi: grazer-skill" \
  --platforms clawsta
```

## 7. Update CLAUDE.md

Add to `/home/scott/CLAUDE.md`:

```markdown
## Grazer Skill (2026-02-06)

- **Name**: Grazer 🐄
- **Purpose**: Multi-platform content discovery for AI agents
- **GitHub**: https://github.com/Scottcjn/grazer-skill
- **NPM**: @elyanlabs/grazer
- **PyPI**: grazer-skill
- **Platforms**: BoTTube, Moltbook, ClawCities, Clawsta
- **Download Tracking**: BoTTube skill tracker
```

## Quick Publish Script

Use the automated script:

```bash
cd /home/scott/grazer-skill
./publish.sh
```

This will:
1. Build TypeScript
2. Run tests
3. Publish to NPM
4. Build Python wheel
5. Publish to PyPI
6. Create Git tag
7. Push to GitHub
