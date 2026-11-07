from datetime import datetime
from bot_detector import analisis_jaringan_dan_bot

class AgentEarlyWarning:
    def __init__(self):
        self.name = "Agen 1 - Early Warning & Anomaly"

    def execute(self, state: dict) -> dict:
        total_data = len(state["raw_data"])
        # Deteksi lonjakan: jika terdapat >= 4 percakapan dalam sampel singkat
        is_deliberate = total_data >= 4
        finding = (
            "Terdeteksi anomali lonjakan narasi dalam rentang waktu singkat (Pola: Deliberate/Digerakkan)."
            if is_deliberate else "Aktivitas percakapan berada pada ambang batas wajar (Organik)."
        )
        return {
            "status": "COMPLETED",
            "anomaly_detected": is_deliberate,
            "finding": finding
        }

class AgentHoaxSentiment:
    def __init__(self):
        self.name = "Agen 2 - Hoax & Sentiment Classifier"

    def execute(self, state: dict) -> dict:
        keywords_hoax = ["rekayasa", "aparat", "jangan percaya", "ditutupi"]
        negative_count = 0
        hoax_indicators = 0

        for item in state["raw_data"]:
            teks = item["isi_komentar"].lower()
            if any(k in teks for k in keywords_hoax):
                hoax_indicators += 1
                negative_count += 1
            elif "aman" in teks or "kondusif" in teks:
                pass
            else:
                negative_count += 0.5

        total = max(1, len(state["raw_data"]))
        neg_pct = min(90, int((negative_count / total) * 100))
        pos_pct = max(5, int((100 - neg_pct) * 0.4))
        neu_pct = 100 - neg_pct - pos_pct

        return {
            "status": "COMPLETED",
            "sentiment": {"positive": pos_pct, "neutral": neu_pct, "negative": neg_pct},
            "hoax_probability": f"{min(95, hoax_indicators * 25)}% (Indikasi fabrikasi narasi terorganisir)"
        }

class AgentBotRadarOSINT:
    def __init__(self):
        self.name = "Agen 3 - BotRadar, SNA & OSINT Hunter"

    def execute(self, state: dict) -> dict:
        hasil_sna = analisis_jaringan_dan_bot(state["csv_path"])
        flagged = hasil_sna["flagged_accounts"]
        mastermind = flagged[0]["username"] if flagged else None

        osint_data = None
        if mastermind:
            # Simulasi modul OSINT (pencarian jejak footprint lintas entitas)
            osint_data = {
                "mastermind_target": mastermind,
                "digital_footprint": ["X / Twitter", "Telegram Group", "TikTok Mirror"],
                "pola_utama": "posting serentak, akun baru",
                "cluster_span": "Selisih waktu unggah < 10 detik"
            }

        return {
            "status": "COMPLETED",
            "detected_pattern": "posting serentak, akun baru",
            "flagged_accounts": flagged,
            "network_graph": hasil_sna["network_graph"],
            "osint_trace": osint_data
        }

class AgentValidatorReporter:
    def __init__(self):
        self.name = "Agen 4 - Validator & PoC Reporter"

    def execute(self, state: dict) -> dict:
        bot_count = len(state["agent_3"]["flagged_accounts"])
        is_anomaly = state["agent_1"]["anomaly_detected"]
        neg_sentiment = state["agent_2"]["sentiment"]["negative"]

        # Penentuan level ancaman berjenjang
        if bot_count >= 3 and is_anomaly and neg_sentiment >= 60:
            threat = "CRITICAL"
        elif bot_count >= 1 or neg_sentiment >= 50:
            threat = "HIGH"
        elif is_anomaly:
            threat = "MEDIUM"
        else:
            threat = "LOW"

        top_actor = (
            state["agent_3"]["flagged_accounts"][0]["username"]
            if bot_count > 0 else "Tidak teridentifikasi"
        )
        
        poc_summary = (
            f"Tervalidasi {bot_count} akun klaster bot berkoordinasi aktif. "
            f"Simpul penyebaran utama berpusat pada entitas {top_actor}."
        )

        return {
            "status": "COMPLETED",
            "threat_level": threat,
            "poc_summary": poc_summary,
            "recommendation": "Isolasi amplifikasi narasi dan lakukan penelusuran lebih lanjut pada akun simpul utama."
        }

class BossAIOps:
    """Komandan orkestrator yang mengarahkan alur kerja antar-agen."""
    def __init__(self):
        self.agen_1 = AgentEarlyWarning()
        self.agen_2 = AgentHoaxSentiment()
        self.agen_3 = AgentBotRadarOSINT()
        self.agen_4 = AgentValidatorReporter()

    def run_investigation(self, topic: str, csv_path: str, raw_data: list) -> dict:
        # Inisialisasi State Board
        state = {
            "topic": topic,
            "csv_path": csv_path,
            "raw_data": raw_data,
            "agent_1": None,
            "agent_2": None,
            "agent_3": None,
            "agent_4": None
        }

        # Eksekusi berurutan (Waterfall Agent Delegation)
        state["agent_1"] = self.agen_1.execute(state)
        state["agent_2"] = self.agen_2.execute(state)
        state["agent_3"] = self.agen_3.execute(state)
        state["agent_4"] = self.agen_4.execute(state)

        return {
            "boss_ai_status": f"Misi analitik selesai untuk target: {topic}.",
            "topic": topic,
            "threat_level": state["agent_4"]["threat_level"],
            "summary_poc": state["agent_4"]["poc_summary"],
            "agent_workflow": [
                {"agent": self.agen_1.name, **state["agent_1"]},
                {"agent": self.agen_2.name, **state["agent_2"]},
                {"agent": self.agen_3.name, **state["agent_3"]},
                {"agent": self.agen_4.name, **state["agent_4"]}
            ]
        }