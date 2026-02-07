# 🐄 Grazer Publishing Checklist

## ✅ Completed

- [x] GitHub repo created and pushed
- [x] Code complete with all features
- [x] Documentation (README, INTEGRATION, DEPLOY)
- [x] BoTTube.ai links added
- [x] TypeScript built
- [x] Python wheel built
- [x] Posted to Moltbook, Clawsta, ClawCities

## 🔄 Ready to Publish

### 1. NPM Publication

```bash
cd /home/scott/grazer-skill

# Login to NPM (one time)
npm login
# Username: (your NPM username)
# Password: (your NPM password)
# Email: scott@elyanlabs.ai

# Publish
npm publish --access public

# Verify
npm view @elyanlabs/grazer
```

### 2. PyPI Publication

```bash
cd /home/scott/grazer-skill

# Install twine (if not installed)
pip install twine

# Upload to PyPI
python3 -m twine upload dist/*
# Username: __token__
# Password: (your PyPI token)

# Verify
pip search grazer-skill
```

### 3. ClawHub Registration

```bash
# Using ClawHub CLI or API
curl -X POST https://clawhub.ai/api/skills \
  -H "Authorization: Bearer clh_w2cSUND_qu_ZUqusQqKV97-s2tROfJ5rsCxKbfQFVy4" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "grazer",
    "description": "Multi-platform content discovery for AI agents",
    "version": "1.0.0",
    "tags": ["content-discovery", "ai-agents", "social-media"],
    "platforms": ["bottube", "moltbook", "clawcities", "clawsta"],
    "npm_package": "@elyanlabs/grazer",
    "pypi_package": "grazer-skill",
    "github_repo": "Scottcjn/grazer-skill"
  }'
```

### 4. Bot Integration Configs Created

Location: `/home/scott/grazer-configs/`

- `moltbook-bot-config.json` - For VPS .131
- `bottube-agent-config.json` - For VPS .153
- `claw-ai-config.json` - For Mac M2
- `sophia-config.json` - For Godot voice bridge

### 5. Auto-Response Enabled

Default: `"auto_respond": false` (safe start)

To enable: Edit `~/.grazer/config.json` and set `"auto_respond": true`

### 6. Monitoring Setup

Training data location: `~/.grazer/training.json`

Monitor with:
```bash
# View training stats
cat ~/.grazer/training.json | jq '.patterns'

# Watch agent loop live
tail -f ~/.grazer/agent.log
```

## 🎯 Post-Publication Steps

- [ ] Update BoTTube skill page with download stats
- [ ] Post announcement on X/Twitter (after rate limit reset)
- [ ] Add to Elyan Labs website
- [ ] Create demo video
- [ ] Write blog post

## 📊 Success Metrics

Target for first week:
- 10+ NPM downloads
- 5+ PyPI installs
- 3+ GitHub stars
- Listed on ClawHub trending

## 🔗 Quick Links

- NPM: https://npmjs.com/package/@elyanlabs/grazer
- PyPI: https://pypi.org/project/grazer-skill/
- GitHub: https://github.com/Scottcjn/grazer-skill
- BoTTube: https://bottube.ai/skills/grazer
- ClawHub: https://clawhub.ai/skills/grazer
