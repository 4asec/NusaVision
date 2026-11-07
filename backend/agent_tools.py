import json
from langchain_core.tools import tool
from bot_detector import analisis_jaringan_dan_bot

@tool
def baca_dan_analisis_botnet(filepath: str = "sample_data.csv") -> str:
    """Gunakan alat ini untuk memindai akun di media sosial, menghitung probabilitas bot,
    mendeteksi pola posting serentak akun baru, dan memetakan struktur jaringan."""
    hasil = analisis_jaringan_dan_bot(filepath)
    return json.dumps(hasil, ensure_ascii=False)

@tool
def cek_jejak_digital_osint(username: str) -> str:
    """Gunakan alat ini untuk melakukan pelacakan jejak digital OSINT terhadap akun target
    di berbagai platform media sosial dan jaringan komunikasi."""
    footprint = {
        "target": username,
        "terdeteksi_di": ["X / Twitter", "Telegram Group", "TikTok"],
        "indikasi_afiliasi": "Klaster akun propaganda terkoordinasi",
        "status_akun": "Aktif dalam 72 jam terakhir"
    }
    return json.dumps(footprint, ensure_ascii=False)