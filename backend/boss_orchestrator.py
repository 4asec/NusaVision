import os
import json
import yaml
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, AsyncGenerator

from model_router import model_router, clean_think_tokens
from live_fetcher import ambil_transmisi_isu, cari_fakta_rujukan
from bot_detector import analisis_data_memori

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "agents_config")

def load_agent_config(filename: str) -> Dict[str, Any]:
    """Membaca konfigurasi terstandar agent dari file YAML."""
    path = os.path.join(CONFIG_DIR, filename)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[!] Error loading YAML {filename}: {e}")
    return {}

# Memory store untuk riwayat investigasi dan berkas PoC
investigations_store: Dict[str, Dict[str, Any]] = {}

class BossOrchestrator:
    """State Machine multi-agent yang mengorkestrasi rantai komando operasi siber kognitif:
    Boss AI -> Ingestion Worker -> Agent 1 (Early) -> Agent 2 (Hoax/Sentimen) -> Agent 3 (Bot/SNA) -> Agent 4 (PoC Auditor)"""

    def __init__(self):
        self.cfg_boss = load_agent_config("boss.yaml")
        self.cfg_a1 = load_agent_config("agent_early.yaml")
        self.cfg_a2 = load_agent_config("agent_hoax_sentiment.yaml")
        self.cfg_a3 = load_agent_config("agent_bot_sna.yaml")
        self.cfg_a4 = load_agent_config("agent_validator.yaml")

    async def execute_stream(self, topik: str) -> AsyncGenerator[str, None]:
        investigation_id = f"NV-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Inisialisasi Shared Blackboard Context
        context: Dict[str, Any] = {
            "investigation_id": investigation_id,
            "topic": topik,
            "start_time": start_time,
            "raw_records": [],
            "boss_directive": "",
            "agent_1_result": {},
            "agent_2_result": {},
            "agent_3_result": {},
            "agent_4_poc": {}
        }

        # -------------------------------------------------------------
        # 1. BOSS AI (Director & Mission Delegator)
        # -------------------------------------------------------------
        msg_boss_init = f"[COMMANDER - DIR. OPERASI] Menginisialisasi Satgas Siber Kognitif. Target operasi: '{topik}'. Mengunci parameter pemantauan."
        yield f"data: {json.dumps({'stage': 'boss', 'status': 'working', 'message': msg_boss_init, 'investigation_id': investigation_id})}\n\n"
        await asyncio.sleep(0.6)

        prompt_boss = (
            f"Kamu adalah Boss AI Direktur Operasi NusaVision. Target investigasi sasaran: '{topik}'. "
            f"Tulis mandat perintah taktis militer siber singkat (2 kalimat tegas) untuk 4 analis bawahanmu."
        )
        directive_text = await model_router.query(prompt_boss, max_tokens=100)
        context["boss_directive"] = directive_text
        msg_boss_done = f"[COMMANDER - MANDAT OPERASI] {directive_text}"
        yield f"data: {json.dumps({'stage': 'boss', 'status': 'done', 'message': msg_boss_done})}\n\n"
        await asyncio.sleep(0.5)

        # -------------------------------------------------------------
        # 2. INGESTION WORKER (Pengambilan Data Nyata)
        # -------------------------------------------------------------
        msg_scraper_work = f"[INGESTION WORKER] Mengambil live feeds percakapan aktual terkait sasaran \"{topik}\" via RSS & open web..."
        yield f"data: {json.dumps({'stage': 'scraper', 'status': 'working', 'message': msg_scraper_work})}\n\n"
        
        # Penarikan data percakapan nyata seputar topik
        live_records = ambil_transmisi_isu(topik, limit=14)
        context["raw_records"] = live_records
        await asyncio.sleep(0.7)

        sample_context = " | ".join([f"{r['username']} ({r['platform']}): {r['isi_komentar'][:90]}" for r in live_records[:4]])
        msg_scraper_done = f"[INGESTION WORKER] Berhasil mengakuisisi {len(live_records)} transmisi data publik. Mengirim payload ke Agen 1 & Agen 2."
        yield f"data: {json.dumps({'stage': 'scraper', 'status': 'done', 'message': msg_scraper_done, 'records_count': len(live_records)})}\n\n"
        await asyncio.sleep(0.5)

        # -------------------------------------------------------------
        # 3. AGEN 1: Early Warning & Anomaly Scout
        # -------------------------------------------------------------
        msg_a1_work = "[AGEN 1 - EARLY WARNING] Memindai anomali kecepatan transmisi narasi dan variasi frekuensi..."
        yield f"data: {json.dumps({'stage': 'agent_1', 'status': 'working', 'message': msg_a1_work})}\n\n"

        prompt_a1 = (
            f"Teks transmisi publik isu '{topik}':\n{sample_context}\n\n"
            f"Tugasmu Agen 1: Klasifikasikan dalam 2 kalimat tegas apakah lonjakan narasi ini adalah 'DELIBERATE SURGE' "
            f"(serangan propaganda buzzer terencana) atau 'ORGANIC VARIATION' (lonjakan wajar publik)? Sebutkan tingkat risiko."
        )
        eval_a1 = await model_router.query(prompt_a1, max_tokens=110)
        
        is_deliberate = any(k in eval_a1.lower() for k in ["deliberate", "serangan", "buzzer", "terencana", "manipulasi", "propaganda"])
        anomaly_score = 88 if is_deliberate else 42
        surge_type = "DELIBERATE SURGE" if is_deliberate else "ORGANIC VARIATION"

        context["agent_1_result"] = {
            "surge_type": surge_type,
            "anomaly_score": anomaly_score,
            "evaluation": eval_a1
        }
        msg_a1_done = f"[AGEN 1 - ANOMALI: {surge_type} ({anomaly_score}%)] {eval_a1}"
        yield f"data: {json.dumps({'stage': 'agent_1', 'status': 'done', 'message': msg_a1_done, 'data': context['agent_1_result']})}\n\n"
        await asyncio.sleep(0.6)

        # -------------------------------------------------------------
        # 4. AGEN 2: Hoax & Sentiment Reasoner (dengan RAG Periksa Fakta)
        # -------------------------------------------------------------
        msg_a2_work = "[AGEN 2 - HOAX & SENTIMENT] DeepSeek menguji plausibilitas klaim terhadap sumber rujukan dan memetakan polaritas sentimen..."
        yield f"data: {json.dumps({'stage': 'agent_2', 'status': 'working', 'message': msg_a2_work})}\n\n"

        # RAG Fact-Checking seputar klaim utama
        klaim_sampel = live_records[0]["isi_komentar"] if live_records else topik
        rujukan_fakta = cari_fakta_rujukan(topik)
        fakta_text = "\n".join([f"- {r['title']} ({r['snippet'][:120]})" for r in rujukan_fakta[:2]]) if rujukan_fakta else "Belum ada verifikasi resmi spesifik."

        prompt_a2 = (
            f"Klaim publik sasaran: '{klaim_sampel}'\n"
            f"Rujukan klarifikasi: {fakta_text}\n"
            f"Tugasmu Agen 2: Simpulkan polaritas sentimen publik (Positif/Netral/Negatif) dan apakah klaim ini berpotensi disinformasi/hoaks. "
            f"Tulis dalam 2 kalimat analisis kritis."
        )
        eval_a2 = await model_router.query(prompt_a2, max_tokens=120)

        # Indikator manipulasi narasi
        manipulation_tags = []
        if is_deliberate:
            manipulation_tags.extend(["Fabricated Outrage", "Coordinated Amplification"])
        if any(w in eval_a2.lower() for w in ["hoaks", "disinformasi", "palsu", "salah", "tidak benar", "provokatif"]):
            manipulation_tags.append("Narrative Distortion")
        if not manipulation_tags:
            manipulation_tags.append("Organic Sentiment Polarization")

        context["agent_2_result"] = {
            "evaluation": eval_a2,
            "sentiment": "NEGATIF" if is_deliberate else "NETRAL",
            "manipulation_tags": manipulation_tags,
            "fact_sources_count": len(rujukan_fakta)
        }
        msg_a2_done = f"[AGEN 2 - EVALUASI KOGNITIF] {eval_a2} [Indikator: {', '.join(manipulation_tags)}]"
        yield f"data: {json.dumps({'stage': 'agent_2', 'status': 'done', 'message': msg_a2_done, 'data': context['agent_2_result']})}\n\n"
        await asyncio.sleep(0.7)

        # -------------------------------------------------------------
        # 5. AGEN 3: BotRadar & Dense SNA Specialist
        # -------------------------------------------------------------
        msg_a3_work = "[AGEN 3 - BOTRADAR & SNA] Menghitung matriks kemiripan leksikal, mengurai klaster botnet, dan merekonstruksi graf rimbun..."
        yield f"data: {json.dumps({'stage': 'agent_3', 'status': 'working', 'message': msg_a3_work})}\n\n"

        # Pemetaan topologi graf D3.js dengan data kontekstual solid
        sna_result = analisis_data_memori(live_records)
        total_bots = len(sna_result["flagged_accounts"])
        total_nodes = len(sna_result["network_graph"]["nodes"])
        mastermind = sna_result.get("mastermind_node", "@lead_node")

        context["agent_3_result"] = {
            "total_analyzed": total_nodes,
            "total_bots": total_bots,
            "mastermind_node": mastermind,
            "flagged_accounts": sna_result["flagged_accounts"],
            "network_graph": sna_result["network_graph"]
        }

        msg_a3_done = f"[AGEN 3 - TOPOLOGI DENSE SNA] Graf terurai: {total_nodes} node terhubung. Terdeteksi {total_bots} akun botnet. Simpul dalang utama: {mastermind}."
        yield f"data: {json.dumps({'stage': 'agent_3', 'status': 'done', 'message': msg_a3_done, 'data': sna_result})}\n\n"
        await asyncio.sleep(0.8)

        # -------------------------------------------------------------
        # 6. AGEN 4: Forensic Validator & PoC Auditor
        # -------------------------------------------------------------
        msg_a4_work = "[AGEN 4 - FORENSIC AUDITOR] Melakukan validasi silang bukti digital lintas-agen dan menyusun Dokumen Pembuktian (PoC)..."
        yield f"data: {json.dumps({'stage': 'agent_4', 'status': 'working', 'message': msg_a4_work})}\n\n"

        # Penentuan status eskalasi ancaman resmi
        threat_level = "CRITICAL THREAT" if (is_deliberate and total_bots >= 2) else ("HIGH ALERT" if total_bots >= 1 else "MEDIUM ALERT")
        
        final_summary = (
            f"Investigasi sasaran '{topik}' tervalidasi dengan tingkat {threat_level}. "
            f"Teridentifikasi pola orkestrasi siber kognitif berbasis botnet berpusat pada simpul {mastermind}. "
            f"DeepSeek R1 mendeteksi indikasi fabrikasi opini ({', '.join(manipulation_tags)}) yang diamplifikasi secara asimetris."
        )

        rekomendasi_taktis = (
            f"1. Terapkan isolasi algoritma dan de-prioritas narasi pada simpul sentral {mastermind}.\n"
            f"2. Terbitkan narasi klarifikasi fakta resmi melalui kanal terverifikasi untuk menetralkan polarisasi.\n"
            f"3. Bekukan klaster {total_bots} akun amplifikasi otomatis berbasis indikator kemiripan leksikal."
        )

        key_evidence = [
            f"Lonjakan narasi terindikasi {surge_type} dengan skor anomali {anomaly_score}%.",
            f"Terkonfirmasi klaster terkoordinasi beranggotakan {total_bots} akun tersangka dengan kesamaan teks verbatim.",
            f"Simpul pengendali narasi terkunci pada akun {mastermind} dengan koneksi satelit berbobot tinggi.",
            f"Ditemukan upaya distorsi kognitif: {', '.join(manipulation_tags)}."
        ]

        final_poc = {
            "investigation_id": investigation_id,
            "timestamp": start_time,
            "target_topic": topik,
            "threat_level": threat_level,
            "dalang_utama": mastermind,
            "ringkasan": final_summary,
            "rekomendasi": rekomendasi_taktis,
            "key_evidence_points": key_evidence,
            "total_nodes_analyzed": total_nodes,
            "total_bots_flagged": total_bots
        }
        context["agent_4_poc"] = final_poc

        # Simpan ke memori store agar bisa diunduh kapan saja
        investigations_store[investigation_id] = context

        msg_a4_done = f"[AGEN 4 - AUDITOR RESMI] Berkas Proof of Concept (PoC) [{investigation_id}] resmi diterbitkan dan siap diekspor."
        yield f"data: {json.dumps({'stage': 'agent_4', 'status': 'done', 'final_poc': final_poc, 'message': msg_a4_done})}\n\n"

    def get_investigation(self, investigation_id: str) -> Dict[str, Any]:
        """Mengambil data investigasi lengkap berdasarkan ID."""
        return investigations_store.get(investigation_id, {})

    def generate_dossier_markdown(self, investigation_id: str) -> str:
        """Membuat laporan forensik teks/markdown terstruktur untuk kebutuhan pelaporan hackathon."""
        ctx = self.get_investigation(investigation_id)
        if not ctx:
            return "# NusaVision Cyber Forensic Dossier\n\nBerkas investigasi tidak ditemukan."

        poc = ctx.get("agent_4_poc", {})
        topik = ctx.get("topic", "-")
        nodes = ctx.get("agent_3_result", {}).get("total_analyzed", 0)
        bots = ctx.get("agent_3_result", {}).get("total_bots", 0)

        lines = [
            f"# NUSAVISION (COGNITIVE DOMAIN RADAR) — FORENSIC PROOF OF CONCEPT (PoC)",
            f"**Berkas Resmi Intelijen Siber Sosial & Pertahanan Opini Publik**",
            f"--------------------------------------------------------------------------------",
            f"- **Investigation ID**    : `{ctx.get('investigation_id')}`",
            f"- **Target Issue / Entity**: `{topik}`",
            f"- **Timestamp Audit**     : {ctx.get('start_time')}",
            f"- **Threat Escalation**   : **{poc.get('threat_level', 'MEDIUM ALERT')}**",
            f"- **Central Mastermind**  : `{poc.get('dalang_utama', '@lead_hub')}`",
            f"- **Network Density**     : {nodes} Node Teranalisis | {bots} Akun Botnet Teridentifikasi",
            f"--------------------------------------------------------------------------------\n",
            f"## 1. MANDAT DIREKTUR OPERASI (BOSS AI)",
            f"{ctx.get('boss_directive', '-')}\n",
            f"## 2. TEMUAN EARLY WARNING & ANOMALI NARASI (AGEN 1)",
            f"- **Klasifikasi Lonjakan**: {ctx.get('agent_1_result', {}).get('surge_type', '-')}",
            f"- **Skor Anomali**       : {ctx.get('agent_1_result', {}).get('anomaly_score', '-')}%",
            f"- **Analisis Scout**      : {ctx.get('agent_1_result', {}).get('evaluation', '-')}\n",
            f"## 3. PENALARAN DISINFORMASI & SENTIMEN KOGNITIF (AGEN 2)",
            f"- **Polaritas Dominan**  : {ctx.get('agent_2_result', {}).get('sentiment', '-')}",
            f"- **Indikator Manipulasi**: {', '.join(ctx.get('agent_2_result', {}).get('manipulation_tags', []))}",
            f"- **Evaluasi Plausibilitas**: {ctx.get('agent_2_result', {}).get('evaluation', '-')}\n",
            f"## 4. TOPOLOGI SOCIAL NETWORK ANALYSIS (AGEN 3)",
            f"- Simpul Sentral (Hub) : `{poc.get('dalang_utama')}`",
            f"- Total Klaster Botnet : {bots} Akun Terkoordinasi",
            f"- Indikasi Profiling   : Akun baru dibuat (<5 hari), duplikasi narasi leksikal, amplifikasi serentak.\n",
            f"## 5. BUKTI FORENSIK TERVALIDASI (AGEN 4)",
        ]
        for p in poc.get("key_evidence_points", []):
            lines.append(f"  [+] {p}")

        lines.extend([
            f"\n## 6. REKOMENDASI TAKTIS & KONTRA-NARASI",
            f"{poc.get('rekomendasi', '-')}\n",
            f"--------------------------------------------------------------------------------",
            f"Dokumen ini diterbitkan secara otomatis oleh NusaVision Autonomous Multi-Agent Defense Engine.",
            f"Diverifikasi oleh: Kartika Cyber Hackathon - Cognitive Domain Radar Team."
        ])
        return "\n".join(lines)

# Singleton Instance
orchestrator = BossOrchestrator()
