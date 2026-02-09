"""
Grazer ImageGen - SVG generation for 4claw posts

Supports three backends:
  1. LLM-based: Any OpenAI-compatible API generates SVG from text prompts
  2. Template-based: Pre-built SVG templates (no external dependencies)
  3. Local: ComfyUI/Stable Diffusion with raster-to-SVG conversion

4claw constraints: SVG only, max 4KB, raw markup, max 1 per post.
"""

import hashlib
import math
import re
from typing import Optional, Dict, List

import requests

# 4claw limits
SVG_MAX_BYTES = 4096
SVG_NAMESPACE = 'xmlns="http://www.w3.org/2000/svg"'

# ─────────────────────────────────────────────────────────────
# SVG Templates (zero-dependency fallback)
# ─────────────────────────────────────────────────────────────

TEMPLATES = {
    "circuit": lambda title, colors: f'''<svg {SVG_NAMESPACE} viewBox="0 0 200 200" width="200" height="200">
<rect width="200" height="200" fill="{colors[0]}"/>
<g stroke="{colors[1]}" stroke-width="1.5" fill="none" opacity="0.6">
<path d="M20,100 H80 L100,80 H180"/><path d="M20,60 H60 L80,40 H140 L160,60 H180"/>
<path d="M20,140 H50 L70,160 H120 L140,140 H180"/><path d="M100,20 V60 L120,80 V140 L100,160 V180"/>
</g>
<g fill="{colors[1]}"><circle cx="80" cy="100" r="3"/><circle cx="100" cy="80" r="3"/>
<circle cx="140" cy="60" r="3"/><circle cx="120" cy="80" r="3"/><circle cx="100" cy="160" r="3"/>
</g>
<text x="100" y="105" text-anchor="middle" fill="{colors[2]}" font-family="monospace" font-size="11">{_truncate(title,20)}</text>
</svg>''',

    "wave": lambda title, colors: f'''<svg {SVG_NAMESPACE} viewBox="0 0 200 120" width="200" height="120">
<defs><linearGradient id="wg" x1="0" y1="0" x2="1" y2="1">
<stop offset="0%" stop-color="{colors[0]}"/><stop offset="100%" stop-color="{colors[1]}"/>
</linearGradient></defs>
<rect width="200" height="120" fill="url(#wg)"/>
<path d="M0,80 Q50,40 100,80 T200,80 V120 H0Z" fill="{colors[2]}" opacity="0.3"/>
<path d="M0,90 Q50,60 100,90 T200,90 V120 H0Z" fill="{colors[2]}" opacity="0.2"/>
<text x="100" y="55" text-anchor="middle" fill="#fff" font-family="sans-serif" font-size="13" font-weight="bold">{_truncate(title,22)}</text>
</svg>''',

    "grid": lambda title, colors: f'''<svg {SVG_NAMESPACE} viewBox="0 0 200 200" width="200" height="200">
<rect width="200" height="200" fill="{colors[0]}"/>
<g stroke="{colors[1]}" stroke-width="0.5" opacity="0.15">
{"".join(f'<line x1="0" y1="{y}" x2="200" y2="{y}"/>' for y in range(0,201,20))}
{"".join(f'<line x1="{x}" y1="0" x2="{x}" y2="200"/>' for x in range(0,201,20))}
</g>
<circle cx="100" cy="90" r="35" fill="none" stroke="{colors[2]}" stroke-width="2"/>
<circle cx="100" cy="90" r="20" fill="{colors[2]}" opacity="0.3"/>
<text x="100" y="150" text-anchor="middle" fill="{colors[2]}" font-family="monospace" font-size="11">{_truncate(title,22)}</text>
</svg>''',

    "badge": lambda title, colors: f'''<svg {SVG_NAMESPACE} viewBox="0 0 200 60" width="200" height="60">
<rect width="200" height="60" rx="8" fill="{colors[0]}"/>
<rect x="2" y="2" width="196" height="56" rx="6" fill="none" stroke="{colors[1]}" stroke-width="1" opacity="0.4"/>
<text x="100" y="36" text-anchor="middle" fill="{colors[2]}" font-family="sans-serif" font-size="14" font-weight="bold">{_truncate(title,24)}</text>
</svg>''',

    "terminal": lambda title, colors: f'''<svg {SVG_NAMESPACE} viewBox="0 0 220 130" width="220" height="130">
<rect width="220" height="130" rx="6" fill="#1a1a2e"/>
<rect x="0" y="0" width="220" height="24" rx="6" fill="#16213e"/>
<circle cx="14" cy="12" r="5" fill="#e94560"/><circle cx="30" cy="12" r="5" fill="#f5a623"/><circle cx="46" cy="12" r="5" fill="#7ec850"/>
<text x="10" y="50" fill="#0f3" font-family="monospace" font-size="11">$ grazer discover</text>
<text x="10" y="68" fill="#0f3" font-family="monospace" font-size="10" opacity="0.7">&gt; {_truncate(title,26)}</text>
<rect x="10" y="80" width="8" height="14" fill="#0f3" opacity="0.8">
<animate attributeName="opacity" values="0.8;0.2;0.8" dur="1.2s" repeatCount="indefinite"/>
</rect>
</svg>''',
}

# Color palettes keyed by vibe
PALETTES = {
    "tech":    ["#0d1117", "#58a6ff", "#c9d1d9"],
    "crypto":  ["#1a1a2e", "#e94560", "#f5f5f5"],
    "retro":   ["#2d1b69", "#ff6ec7", "#00ff9f"],
    "nature":  ["#1b4332", "#52b788", "#d8f3dc"],
    "dark":    ["#0a0a0a", "#bb86fc", "#e0e0e0"],
    "fire":    ["#1a0000", "#ff4500", "#ffd700"],
    "ocean":   ["#0a1628", "#00bcd4", "#e0f7fa"],
    "default": ["#1e1e2e", "#cba6f7", "#cdd6f4"],
}


def _truncate(text: str, maxlen: int) -> str:
    """XML-safe truncation."""
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
    if len(text) > maxlen:
        return text[:maxlen - 1] + "~"
    return text


def _hash_seed(text: str) -> int:
    """Deterministic seed from text."""
    return int(hashlib.md5(text.encode()).hexdigest()[:8], 16)


def _pick_template(prompt: str) -> str:
    """Pick a template based on prompt content."""
    lower = prompt.lower()
    if any(w in lower for w in ["code", "terminal", "cli", "shell", "hack", "dev"]):
        return "terminal"
    if any(w in lower for w in ["crypto", "blockchain", "token", "mining", "defi"]):
        return "circuit"
    if any(w in lower for w in ["badge", "label", "tag", "status"]):
        return "badge"
    if any(w in lower for w in ["wave", "music", "audio", "vibe", "chill"]):
        return "wave"
    # Deterministic fallback
    names = list(TEMPLATES.keys())
    return names[_hash_seed(prompt) % len(names)]


def _pick_palette(prompt: str) -> List[str]:
    """Pick a color palette based on prompt content."""
    lower = prompt.lower()
    for key in PALETTES:
        if key in lower:
            return PALETTES[key]
    # Deterministic fallback
    keys = list(PALETTES.keys())
    return PALETTES[keys[_hash_seed(prompt) % len(keys)]]


def _validate_svg(svg: str) -> str:
    """Validate and sanitize SVG for 4claw."""
    svg = svg.strip()
    # Must start with <svg
    if not svg.startswith("<svg"):
        raise ValueError("Generated content is not valid SVG")
    # Ensure xmlns is present
    if 'xmlns=' not in svg:
        svg = svg.replace("<svg", f'<svg {SVG_NAMESPACE}', 1)
    # Size check
    if len(svg.encode("utf-8")) > SVG_MAX_BYTES:
        raise ValueError(f"SVG exceeds 4KB limit ({len(svg.encode('utf-8'))} bytes)")
    return svg


# ─────────────────────────────────────────────────────────────
# Template Generator (zero-dependency)
# ─────────────────────────────────────────────────────────────

def generate_template_svg(prompt: str, template: Optional[str] = None,
                          palette: Optional[str] = None) -> str:
    """Generate SVG from built-in templates. No API calls needed.

    Args:
        prompt: Text description / title for the image
        template: Force a specific template (circuit, wave, grid, badge, terminal)
        palette: Force a color palette (tech, crypto, retro, nature, dark, fire, ocean)

    Returns:
        Raw SVG string ready for 4claw media field
    """
    tpl_name = template if template and template in TEMPLATES else _pick_template(prompt)
    colors = PALETTES.get(palette, _pick_palette(prompt)) if palette else _pick_palette(prompt)
    svg = TEMPLATES[tpl_name](prompt, colors)
    return _validate_svg(svg)


# ─────────────────────────────────────────────────────────────
# LLM-based SVG Generator (OpenAI-compatible)
# ─────────────────────────────────────────────────────────────

LLM_SVG_SYSTEM_PROMPT = """You are an SVG artist. Generate a single SVG image based on the user's prompt.

STRICT RULES:
- Output ONLY the raw <svg>...</svg> markup. No markdown, no explanation, no code fences.
- Must include xmlns="http://www.w3.org/2000/svg"
- Total SVG must be under 3800 bytes (leave room for wrapper)
- Use viewBox, keep dimensions reasonable (200x200 or similar)
- Use only generic fonts: sans-serif, serif, monospace
- You may use gradients, animations (<animate>, <animateTransform>), and filters
- Make it visually interesting and relevant to the prompt
- Prefer geometric/abstract art that looks good at small sizes"""


def generate_llm_svg(
    prompt: str,
    llm_url: str = "http://100.75.100.89:8080/v1/chat/completions",
    llm_model: str = "gpt-oss-120b",
    llm_api_key: Optional[str] = None,
    temperature: float = 0.8,
    timeout: int = 60,
) -> str:
    """Generate SVG using any OpenAI-compatible LLM endpoint.

    Args:
        prompt: Image description
        llm_url: OpenAI-compatible chat completions endpoint
        llm_model: Model name/ID
        llm_api_key: Optional API key (Bearer token)
        temperature: Creativity (0.0-1.0)
        timeout: Request timeout in seconds

    Returns:
        Raw SVG string ready for 4claw media field
    """
    headers = {"Content-Type": "application/json"}
    if llm_api_key:
        headers["Authorization"] = f"Bearer {llm_api_key}"

    payload = {
        "model": llm_model,
        "messages": [
            {"role": "system", "content": LLM_SVG_SYSTEM_PROMPT},
            {"role": "user", "content": f"Create an SVG image: {prompt}"},
        ],
        "temperature": temperature,
        "max_tokens": 2048,
    }

    resp = requests.post(llm_url, json=payload, headers=headers, timeout=timeout)
    resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"].strip()

    # Extract SVG if wrapped in code fences
    svg_match = re.search(r'<svg[\s\S]*?</svg>', content)
    if not svg_match:
        raise ValueError("LLM did not produce valid SVG output")

    return _validate_svg(svg_match.group(0))


# ─────────────────────────────────────────────────────────────
# Unified generate() — tries LLM first, falls back to template
# ─────────────────────────────────────────────────────────────

def generate_svg(
    prompt: str,
    llm_url: Optional[str] = None,
    llm_model: str = "gpt-oss-120b",
    llm_api_key: Optional[str] = None,
    template: Optional[str] = None,
    palette: Optional[str] = None,
    prefer_llm: bool = True,
) -> Dict:
    """Generate SVG for 4claw posts. Tries LLM, falls back to templates.

    Args:
        prompt: Image description
        llm_url: OpenAI-compatible endpoint (None = skip LLM, use template only)
        llm_model: Model name
        llm_api_key: Optional API key
        template: Force template name
        palette: Force color palette
        prefer_llm: If True and llm_url set, try LLM first

    Returns:
        Dict with 'svg' (raw markup), 'method' (llm/template), 'bytes' (size)
    """
    svg = None
    method = None

    # Try LLM first
    if prefer_llm and llm_url:
        try:
            svg = generate_llm_svg(prompt, llm_url=llm_url, llm_model=llm_model,
                                   llm_api_key=llm_api_key)
            method = "llm"
        except Exception:
            pass  # Fall through to template

    # Fallback to template
    if svg is None:
        svg = generate_template_svg(prompt, template=template, palette=palette)
        method = "template"

    return {
        "svg": svg,
        "method": method,
        "bytes": len(svg.encode("utf-8")),
    }


def svg_to_media(svg: str) -> List[Dict]:
    """Wrap an SVG string into 4claw's media array format.

    Returns:
        List ready to pass as the 'media' field in 4claw API calls
    """
    return [{
        "type": "svg",
        "data": svg,
        "generated": True,
        "nsfw": False,
    }]
