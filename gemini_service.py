import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List


def _load_env_key() -> str:
    """Read GEMINI_API_KEY from environment or local .env file if present."""
    key = (os.environ.get("GEMINI_API_KEY") or "").strip()
    if key:
        return key
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            pass
    return ""


def _extract_inline_image(data_url: str) -> Dict[str, Any] | None:
    """Convert a base64 data URL into a Gemini inlineData part."""
    if not data_url or "," not in data_url:
        return None
    header, b64_data = data_url.split(",", 1)
    mime = "image/png"
    if "image/jpeg" in header or "image/jpg" in header:
        mime = "image/jpeg"
    elif "image/webp" in header:
        mime = "image/webp"
    return {
        "inlineData": {
            "mimeType": mime,
            "data": b64_data.strip(),
        }
    }


def _discover_available_models(api_key: str) -> List[str]:
    """Query Gemini ListModels endpoint to find active models supporting generateContent."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = []
        skip_keywords = ("embedding", "image", "robotics", "tts", "audio", "computer-use", "deep-research", "veo", "imagen")
        for m in data.get("models") or []:
            methods = m.get("supportedGenerationMethods") or []
            name = (m.get("name") or "").replace("models/", "")
            low = name.lower()
            if "generateContent" in methods and "gemini" in low:
                if not any(k in low for k in skip_keywords):
                    models.append(name)
        # Prioritaskan seri 3.8 / 2.5 / flash terlebih dahulu
        models.sort(key=lambda n: (0 if "3.8" in n else (1 if "3." in n else 2), 0 if "flash" in n else 1, n))
        return models
    except Exception:
        return []


def _strip_json_fences(raw_text: str) -> str:
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


def generate_report_ai_content(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Call Gemini API (multimodal) to generate Alat & Bahan, Langkah Kerja, captions, analysis, and review."""
    api_key = (payload.get("apiKey") or "").strip() or _load_env_key()
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY belum dikonfigurasi. Isi Gemini API Key pada kolom AI atau set environment variable GEMINI_API_KEY."
        )

    module_name = (payload.get("moduleName") or payload.get("moduleKey") or "Praktikum").strip()
    module_tools = (payload.get("moduleTools") or "").strip()
    meeting_number = int(payload.get("meetingNumber") or 1)
    topic_title = (payload.get("topicTitle") or "").strip()

    result_images: List[Dict[str, Any]] = payload.get("resultImages") or []
    posttest_images: List[Dict[str, Any]] = payload.get("posttestImages") or []
    code_blocks: List[Dict[str, Any]] = payload.get("codeBlocks") or []
    posttest_code_blocks: List[Dict[str, Any]] = payload.get("posttestCodeBlocks") or []

    code_summary_parts = []
    for idx, cb in enumerate(code_blocks, start=1):
        title = (cb.get("title") or f"Kode Program 2.{idx}").strip()
        code = (cb.get("code") or "").strip()
        if code:
            code_summary_parts.append(f"Kode Program 2.{idx} ({title}):\n{code[:4000]}")
    for idx, cb in enumerate(posttest_code_blocks, start=1):
        title = (cb.get("title") or f"Kode Program 3.{idx} Post Test").strip()
        code = (cb.get("code") or "").strip()
        if code:
            code_summary_parts.append(f"Kode Program 3.{idx} ({title}):\n{code[:4000]}")
    code_summary = "\n\n".join(code_summary_parts) if code_summary_parts else "(Belum ada kode program ditempelkan)"

    mode = (payload.get("mode") or "all").strip().lower()
    if mode == "posttest":
        post_code_summary_parts = []
        for idx, cb in enumerate(posttest_code_blocks, start=1):
            title = (cb.get("title") or f"Kode Program 3.{idx} Post Test").strip()
            code = (cb.get("code") or "").strip()
            if code:
                post_code_summary_parts.append(f"Kode Program 3.{idx} ({title}):\n{code[:4000]}")
        post_code_summary = (
            "\n\n".join(post_code_summary_parts)
            if post_code_summary_parts
            else "(Belum ada kode program Post-Test ditempelkan)"
        )
        prompt_text = f"""Anda adalah asisten dosen praktikum Informatika Universitas Ahmad Dahlan (LabTIF UAD).
Buat konten khusus bagian Post-Test berbahasa Indonesia yang baku, rapi, dan teknis.

Konteks Praktikum:
- Mata Praktikum: {module_name}
- Perangkat/Tools Utama: {module_tools}
- Pertemuan Ke: {meeting_number}
- Materi: {topic_title}
- Jumlah Gambar Post-Test: {len(posttest_images)}
- Jumlah Kode Program Post-Test: {len(posttest_code_blocks)}

Kode Program Post-Test yang Dilampirkan:
{post_code_summary}

Tugas Anda (kembalikan HANYA JSON valid tanpa markdown/penjelasan lain):
1. "posttestImageDescriptions": array string sepanjang {len(posttest_images)} elemen berisi keterangan teknis (1-2 kalimat) untuk setiap Gambar Post-Test sesuai urutan gambar (jangan ubah/buat judul gambar, hanya keterangannya).
2. "posttestCodeBlockDescriptions": array string sepanjang {len(posttest_code_blocks)} elemen berisi penjelasan singkat (1-2 kalimat) mengenai fungsi/alur setiap Kode Program Post-Test sesuai urutan.
3. "posttestAnalysis": string berisi Analisis Hasil Post-Test yang menjelaskan cara kerja program/solusi Post-Test dan output-nya (1-2 paragraf).

Format JSON persis:
{{
  "posttestImageDescriptions": ["..."],
  "posttestCodeBlockDescriptions": ["..."],
  "posttestAnalysis": "..."
}}"""
        parts: List[Dict[str, Any]] = [{"text": prompt_text}]
        for idx, img in enumerate(posttest_images[:4], start=1):
            inline = _extract_inline_image(img.get("dataUrl") or "")
            if inline:
                parts.append({"text": f"[Gambar Post-Test 3.{idx}: {(img.get('title') or '').strip()}]"})
                parts.append(inline)
    else:
        prompt_text = f"""Anda adalah asisten dosen praktikum Informatika Universitas Ahmad Dahlan (LabTIF UAD).
Buat konten laporan praktikum berbahasa Indonesia yang baku, rapi, teknis, dan memenuhi Rubrik Skor 5.

Konteks Praktikum:
- Mata Praktikum: {module_name}
- Perangkat/Tools Utama: {module_tools}
- Pertemuan Ke: {meeting_number}
- Materi: {topic_title}
- Jumlah Gambar Hasil Praktikum: {len(result_images)}
- Jumlah Kode Program Hasil Praktikum: {len(code_blocks)}
- Jumlah Gambar Post-Test: {len(posttest_images)}
- Jumlah Kode Program Post-Test: {len(posttest_code_blocks)}

Kode Program yang Dilampirkan:
{code_summary}

Tugas Anda (kembalikan HANYA JSON valid tanpa markdown/penjelasan lain):
1. "toolsMaterials": array string berisi daftar Alat dan Bahan praktikum (mis. ["Laptop / PC", "Dev C++"] atau sesuai modul & materi).
2. "workSteps": array string berisi 4-8 Langkah Kerja praktikum yang runtut (kalimat operasional formal, mis. "Membuat program C++ dengan ...").
3. "resultImageDescriptions": array string sepanjang {len(result_images)} elemen berisi keterangan teknis singkat (1-2 kalimat) untuk setiap Gambar Hasil Praktikum sesuai urutan gambar yang dikirim.
4. "codeBlockDescriptions": array string sepanjang {len(code_blocks)} elemen berisi penjelasan singkat (1-2 kalimat) untuk setiap Kode Program Hasil Praktikum (Kode Program 2.x) sesuai urutan.
5. "posttestImageDescriptions": array string sepanjang {len(posttest_images)} elemen berisi keterangan teknis singkat untuk setiap Gambar Post-Test sesuai urutan gambar yang dikirim.
6. "posttestCodeBlockDescriptions": array string sepanjang {len(posttest_code_blocks)} elemen berisi penjelasan singkat untuk setiap Kode Program Post-Test (Kode Program 3.x) sesuai urutan.
7. "analysisText": string berisi Analisis Hasil praktikum yang menjelaskan alur kerja program/percobaan, output yang dihasilkan, dan keterkaitannya dengan konsep materi (2-3 paragraf).
8. "posttestAnalysis": string berisi Analisis Hasil Post-Test jika ada gambar atau kode Post-Test (atau "" jika tidak ada).
9. "reviewText": string berisi Ulasan / Refleksi Praktikum memenuhi Rubrik Skor 5 (wajib spesifik memuat: pembelajaran yang didapat, kendala yang dihadapi, solusi yang dilakukan, hasil, serta temuan).

Format JSON persis:
{{
  "toolsMaterials": ["..."],
  "workSteps": ["..."],
  "resultImageDescriptions": ["..."],
  "codeBlockDescriptions": ["..."],
  "posttestImageDescriptions": ["..."],
  "posttestCodeBlockDescriptions": ["..."],
  "analysisText": "...",
  "posttestAnalysis": "...",
  "reviewText": "..."
}}"""

        parts: List[Dict[str, Any]] = [{"text": prompt_text}]
        for idx, img in enumerate(result_images[:6], start=1):
            inline = _extract_inline_image(img.get("dataUrl") or "")
            if inline:
                parts.append({"text": f"[Gambar Hasil Praktikum 2.{idx}: {(img.get('title') or '').strip()}]"})
                parts.append(inline)

        for idx, img in enumerate(posttest_images[:4], start=1):
            inline = _extract_inline_image(img.get("dataUrl") or "")
            if inline:
                parts.append({"text": f"[Gambar Post-Test 3.{idx}: {(img.get('title') or '').strip()}]"})
                parts.append(inline)

    env_model = (os.environ.get("GEMINI_MODEL") or "").strip()
    candidate_models = [env_model] if env_model else ["gemini-3.8-flash"]

    body = json.dumps(
        {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "temperature": 0.4,
                "responseMimeType": "application/json",
            },
        }
    ).encode("utf-8")

    resp_data = None
    last_err = None
    tried = set()
    idx = 0
    discovered = False

    while idx < len(candidate_models):
        model = candidate_models[idx]
        idx += 1
        if not model or model in tried:
            continue
        tried.add(model)

        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        for attempt in range(2):
            req = urllib.request.Request(
                endpoint,
                data=body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    break
            except urllib.error.HTTPError as err:
                detail = err.read().decode("utf-8", errors="ignore")
                if err.code in (503, 429):
                    last_err = RuntimeError(
                        "Server Gemini sedang sibuk / kelebihan beban (503). Silakan tunggu beberapa detik lalu klik Generate lagi."
                    )
                    if attempt == 0:
                        time.sleep(2)
                        continue
                    break
                if err.code == 400 and ("modality" in detail.lower() or "image" in detail.lower()):
                    if last_err is None:
                        last_err = RuntimeError(f"Gemini API error (400): {detail[:300]}")
                    break
                if err.code == 404:
                    if last_err is None:
                        last_err = RuntimeError(f"Gemini API error (404): {detail[:300]}")
                    break
                raise RuntimeError(f"Gemini API error ({err.code}): {detail[:300]}") from err
            except urllib.error.URLError as err:
                raise RuntimeError(f"Gagal menghubungi Gemini API: {err.reason}") from err

        if resp_data is not None:
            break

        # Jika model utama gagal (503/404), temukan model lain yang aktif di API key user
        if not discovered and not env_model:
            discovered = True
            for alt in _discover_available_models(api_key):
                if alt not in tried:
                    candidate_models.append(alt)

    if resp_data is None and len(parts) > 1:
        # Fallback terakhir: coba kirim text-only (tanpa inline gambar) jika model aktif tidak mendukung gambar
        text_only_body = json.dumps(
            {
                "contents": [{"parts": [parts[0]]}],
                "generationConfig": {
                    "temperature": 0.4,
                    "responseMimeType": "application/json",
                },
            }
        ).encode("utf-8")
        for model in candidate_models:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            req = urllib.request.Request(
                endpoint,
                data=text_only_body,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=60) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    break
            except Exception:
                continue

    if resp_data is None:
        raise last_err or RuntimeError("Gagal menghubungi Gemini API.")

    candidates = resp_data.get("candidates") or []
    if not candidates:
        raise RuntimeError("Gemini API tidak mengembalikan kandidat respons.")

    text_parts = [
        p.get("text", "")
        for p in (candidates[0].get("content") or {}).get("parts", [])
        if p.get("text")
    ]
    raw_json = _strip_json_fences("\n".join(text_parts))
    parsed = json.loads(raw_json)

    return {
        "toolsMaterials": [str(x).strip() for x in (parsed.get("toolsMaterials") or []) if str(x).strip()],
        "workSteps": [str(x).strip() for x in (parsed.get("workSteps") or []) if str(x).strip()],
        "resultImageDescriptions": [str(x).strip() for x in (parsed.get("resultImageDescriptions") or [])],
        "codeBlockDescriptions": [str(x).strip() for x in (parsed.get("codeBlockDescriptions") or [])],
        "posttestImageDescriptions": [str(x).strip() for x in (parsed.get("posttestImageDescriptions") or [])],
        "posttestCodeBlockDescriptions": [str(x).strip() for x in (parsed.get("posttestCodeBlockDescriptions") or [])],
        "analysisText": str(parsed.get("analysisText") or "").strip(),
        "posttestAnalysis": str(parsed.get("posttestAnalysis") or "").strip(),
        "reviewText": str(parsed.get("reviewText") or "").strip(),
    }
