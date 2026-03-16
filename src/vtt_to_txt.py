import re
import logging
from pathlib import Path
logger = logging.getLogger(__name__)

class Clean:
    def __init__(self, vtt_dir: Path, txt_dir: Path) -> None:
        self.vtt_dir = vtt_dir
        self.txt_dir = txt_dir
        self.txt_dir.mkdir(parents=True, exist_ok=True)
        self.NOISE_LINES = {
            "WEBVTT", "Kind:", "Language:",
            "[Music]", "[music]", "[Applause]", "[Laughter]",
            "[Cheering]", "[Clapping]", "[Audience Laughing]",
            "[Audience Applause]", "[Background Noise]",
            "[प्रशंसा]", "[तालियाँ]", "[संगीत]",
            "[हँसी]", "[जयकारे]", "[शोर]", "[पृष्ठभूमि संगीत]",
        }
        self._TAG_RE = re.compile(r'<[^>]+>') # Matches inline timing/formatting tags like <00:00:09.360> and <c>text</c>
        self._TIMESTAMP_RE = re.compile(r'^\d{2}:\d{2}:\d{2}[.,]\d{3}\s*-->') # Matches VTT timestamp lines like "00:00:08.360 --> 00:00:21.509 align:start position:0%"

    def clean_file(self, vtt_file: Path) -> list[str]:
        seen_lines = set()
        cleaned = []
        with vtt_file.open("r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped: # Skip empty lines
                    continue
                if self._TIMESTAMP_RE.match(stripped): # Skip timestamp lines
                    continue
                if any(stripped.startswith(k) for k in self.NOISE_LINES): # Skip header and noise lines
                    continue
                clean = self._TAG_RE.sub('', stripped).strip() # Strip inline tags → clean text
                if not clean or clean == ' ': # Skip empty after stripping, single spaces, or pure whitespace
                    continue
                if clean in seen_lines: # Deduplicate — skip if we've seen this exact line already
                    continue
                seen_lines.add(clean)
                cleaned.append(clean)
        return cleaned

    def vtt_to_txt(self) -> None:
        for vtt_file in self.vtt_dir.glob("*.vtt"):
            txt_file = self.txt_dir / vtt_file.with_suffix(".txt").name
            if txt_file.exists():
                logger.info("Skipping %s (already exists)", txt_file.name)
                continue
            cleaned = self.clean_file(vtt_file)
            txt_file.write_text('\n'.join(cleaned) + '\n', encoding='utf-8')
            logger.info("Converted %s → %s (%d lines)", vtt_file.name, txt_file.name, len(cleaned))
        logger.info("Completed %s → %s conversion", self.vtt_dir.name, self.txt_dir.name)
