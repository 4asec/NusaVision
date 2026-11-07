import json
from langchain_ollama import ChatOllama
from agent_tools import baca_dan_analisis_botnet, cek_jejak_digital_osint

class AutonomousCyberOffice:
    def __init__(self):
        # Menggunakan model DeepSeek lokal via Ollama
        self.llm = ChatOllama(
        model="deepseek-r1:8b",
        temperature=0.2,
        num_predict=250  # Batasi agar respon cepat dan tidak bertele-tele
)

    def run_full_mission(self, topic: str):
        log_eksekusi = []

        # 1. BOSS AI (Director & Mission Delegator)
        prompt_boss = (
            f"Kamu adalah Boss AI / Direktur Operasi Siber NusaVision. "
            f"Misi masuk dengan target: '{topic}'. "
            f"Buat pembagian arahan ringkas ke 4 agen analis bawahanmu "
            f"(Agen 1: Early Warning, Agen 2: Hoax/Sentimen, Agen 3: BotRadar/OSINT, Agen 4: Validator/PoC). "
            f"Tulis instruksi dalam 3 kalimat tegas dan taktis."
        )
        resp_boss = self.llm.invoke(prompt_boss)
        log_eksekusi.append({
            "agent": "Boss AI (Director of Operations)",
            "action": "Strategi Komando Operasi",
            "thought": resp_boss.content
        })

        # 2. AGEN 1: Early Warning & Anomaly Scout
        prompt_agen1 = (
            f"Kamu adalah Agen 1 (Early Warning & Anomaly Scout). "
            f"Topik investigasi: '{topic}'. "
            f"Analisis apakah lonjakan percakapan pada topik ini terindikasi deliberate (serangan propaganda yang disengaja) "
            f"atau tren organik publik. Berikan evaluasi ancaman ringkas."
        )
        resp_agen1 = self.llm.invoke(prompt_agen1)
        log_eksekusi.append({
            "agent": "Agen 1 - Early Warning & Anomaly Scout",
            "action": "Deteksi Dini Lonjakan Narasi",
            "thought": resp_agen1.content
        })

        # 3. AGEN 2: Hoax & Sentiment Analyst
        with open("sample_data.csv", "r", encoding="utf-8") as f:
            raw_text = f.read()

        prompt_agen2 = (
            f"Kamu adalah Agen 2 (Pakar Analisis Hoaks & Sentimen). "
            f"Berikut sampel data percakapan terkini:\n{raw_text}\n\n"
            f"Tugasmu: "
            f"1. Klasifikasikan potensi narasi disinformasi/hoaks. "
            f"2. Taksir polaritas sentimen publik (Positif, Netral, Negatif). "
            f"Jawab dengan analisis penalaran kritis."
        )
        resp_agen2 = self.llm.invoke(prompt_agen2)
        log_eksekusi.append({
            "agent": "Agen 2 - Disinformation & Sentiment Analyst",
            "action": "Analisis Hoaks & Opini Publik",
            "thought": resp_agen2.content
        })

        # 4. AGEN 3: BotRadar & OSINT Specialist
        hasil_tool_bot = baca_dan_analisis_botnet.invoke({})
        parsed_bot = json.loads(hasil_tool_bot)

        target_dalang = (
            parsed_bot["flagged_accounts"][0]["username"]
            if parsed_bot["flagged_accounts"] else "@unknown"
        )
        hasil_tool_osint = cek_jejak_digital_osint.invoke({"username": target_dalang})

        prompt_agen3 = (
            f"Kamu adalah Agen 3 (Operator BotRadar & Forensik OSINT). "
            f"Data deteksi botnet:\n{hasil_tool_bot}\n"
            f"Data pelacakan OSINT target dalang {target_dalang}:\n{hasil_tool_osint}\n\n"
            f"Tugasmu: Jelaskan pola 'posting serentak, akun baru' yang ditemukan, "
            f"bagaimana jaringan buzzer ini beroperasi, dan identitas simpul dalang utamanya."
        )
        resp_agen3 = self.llm.invoke(prompt_agen3)
        log_eksekusi.append({
            "agent": "Agen 3 - BotRadar & OSINT Specialist",
            "action": "Investigasi Jaringan & Pelacakan Aktor",
            "thought": resp_agen3.content,
            "raw_tool_data": {
                "flagged_accounts": parsed_bot["flagged_accounts"],
                "network_graph": parsed_bot["network_graph"],
                "osint": json.loads(hasil_tool_osint)
            }
        })

        # 5. AGEN 4: Validator & PoC Reporter
        prompt_agen4 = (
            f"Kamu adalah Agen 4 (Validator & PoC Reporter). "
            f"Evaluasi seluruh laporan intelijen berikut:\n"
            f"- Temuan Agen 1: {resp_agen1.content}\n"
            f"- Temuan Agen 2: {resp_agen2.content}\n"
            f"- Bukti Agen 3: {resp_agen3.content}\n\n"
            f"Tugasmu: Berikan kesimpulan final, tetapkan status ancaman (CRITICAL/HIGH/MEDIUM/LOW), "
            f"dan buat rangkuman Proof of Concept (PoC) tervalidasi untuk komando pertahanan."
        )
        resp_agen4 = self.llm.invoke(prompt_agen4)
        log_eksekusi.append({
            "agent": "Agen 4 - Validator & Forensic Reporter",
            "action": "Validasi Silang & Finalisasi PoC",
            "thought": resp_agen4.content
        })

        return {
            "topic": topic,
            "engine": "DeepSeek Multi-Agent Architecture",
            "mission_status": "SUCCESS",
            "mission_logs": log_eksekusi
        }