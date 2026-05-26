import gradio as gr
import folium
import google.generativeai as genai
import json
import os
import requests
from datetime import datetime
import base64

# File Paths
DB_FILE = "reports.json"

# Seeding illustrative graphics
DEFAULT_PRESETS_GRAPHICS = {
    "pothole": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjNGI1NTYzIi8+PHBhdGggZD0iTTUwIDEyMCBRODAgMTUwIDEyMCAxMjAgVDIwMCAxMzAgVDI1MCAxMDBRMTgwIDYwIDE0MCAxMDBUNTAgMTIwIiBmaWxsPSIjMWYyOTM3Ii8+PGNpcmNsZSBjeD0iMTIwIiBjeT0iMTE1IiByPSIxNSIgZmlsbD0iIzExMTgyNyIvPjxjaXJjbGUgY3g9IjE3MCIgY3k9IjExMCIgcj0iMTAiIGZpbGw9IiMxMTE4MjciLz48dGV4dCB4PSIyMCIgeT0iNDAiIGZpbGw9IndoaXRlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9ImJvbGQiIGZvbnQtc2l6ZT0iMTQiPkRFRVAgUk9BRCBQT1RIT0xEPC90ZXh0Pjwvc3ZnPg==",
    "streetlight": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMTExODI3Ii8+PGxpbmUgeDE9IjE1MCIgeTE9IjUwIiB4Mj0iMTUwIiB5Mj0iMTkwIiBzdHJva2U9IiM2YjcyODAiIHN0cm9rZS13aWR0aD0iNiIvPjxjaXJjbGUgY3g9IjE1MCIgY3k9IjUwIiByPSIxMiIgZmlsbD0iI2VhYjMwOCIgb3BhY2l0eT0iMC4zIi8+PGNpcmNsZSBjeD0iMTUwIiBjeT0iNTAiIHI9IjYiIGZpbGw9IiM5Y2EzYWYiLz48dGV4dCB4PSIyMCIgeT0iNDAiIGZpbGw9IiNmODcxNzEiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iYm9sZCIgZm9udC1zaXplPSIxNCI+QlJPS0VOIFNUUkVFVExJR0hUPC90ZXh0Pjwvc3ZnPg==",
    "parking": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZmVmMmYyIi8+PHJlY3QgeD0iODAiIHk9IjcwIiB3aWR0aD0iMTQwIiBoZWlnaHQ9IjcwIiByeD0iMTAiIGZpbGw9IiNlZjQ0NDQiLz48Y2lyY2xlIGN4PSIxMTAiIGN5PSIxNDAiIHI9IjE4IiBmaWxsPSIjMWYyOTM3Ii8+PGNpcmNsZSBjeD0iMTkwIiBjeT0iMTQwIiByPSIxOCIgZmlsbD0iIzFmMjkzNyIvPjxjaXJjbGUgY3g9IjE1MCIgY3k9IjgwIiBgcj0iMzAiIHN0cm9rZT0iI2I5MWMxYyIgc3Ryb2tlLXdpZHRoPSI4IiBmaWxsPSJub25lIi8+PHRleHQgeD0iMjAiIHk9IjQwIiBmaWxsPSIjYjkxYzFjIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9ImJvbGQiIGZvbnQtc2l6ZT0iMTQiPklMTEVHQUwgUEFSS0lORzwvdGV4dD48L3N2Zz4=",
    "accident": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMWUyOTNiIi8+PHBhdGggZD0iTTQwIDE0MCBMMTMwIDExMCBMMTgwIDEyMCBMMjcwIDE0MCIgc3Ryb2tlPSIjNGI1NTYzIiBzdHJva2Utd2lkdGg9IjgiIGZpbGw9Im5vbmUiLz48cmVjdCB4PSI2MCIsInk9IjkwIiB3aWR0aD0iNjAiIGhlaWdodD0iMzAiIGZpbGw9IiNlZjQ0NDQiLHRyYW5zZm9ybT0icm90YXRlKC0xMCwgNjAsIDkwKSIvPjxyZWN0IHg9IjEyMCIgeT0iODUiIHdpZHRoPSI2MCIgaGVpZ2h0PSIzMCIgZmlsbD0iIzNiODJmNiIgdHJhbnNmb3JtPSJyb3RhdGUoNSwgMTIwLCA4NSkiLz48Y2lyY2xlIGN4PSI3MCIgY3k9IjExNSIgcj0iMTAiIGZpbGw9ImJsYWNrIi8+PGNpcmNsZSBjeD0iMTcwIiBjeT0iMTUxIiByPSIxMCIgZmlsbD0iYmxhY2siLz48dGV4dCB4PSIyMCIgeT0iNDAiIGZpbGw9IiNmODcxNzEiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iYm9sZCIgZm9udC1zaXplPSIxNCI+M19DQVJfQ09MTElTSU9OX09OX0hJR0hXQVk8L3RleHQ+PC9zdmc+"
}

# Seed Data
SEED_REPORTS = [
    {
        "id": "rep-101",
        "title": "경부고속도로 서울방향 서초IC 부근 3중 추돌 사고 발생",
        "category": "교통사고/위험",
        "authority": "고속도로 순찰대/한국도로공사",
        "coords": [37.4842, 127.0178],
        "address": "서울특별시 서초구 서초동 산 112 (경부고속도로 서울방향)",
        "description": "경부고속도로 서울방향 서초IC 전방 약 500미터 지점 2차로상에서 승용차 3대가 연쇄 추돌하는 심각한 사고가 일어났습니다. 사고 차량 파편이 1, 2, 3차로에 넓게 흩어져 있으며 뒤따르는 차량들이 비상등을 켜고 급제동을 하고 있어 연쇄 추가 사고 위험이 큽니다. 사고 직후 극심한 병목 정체가 유발되고 있으며 긴급 사고 처리 및 견인 조치가 조속히 필요합니다.",
        "image": DEFAULT_PRESETS_GRAPHICS["accident"],
        "timestamp": datetime.now().isoformat(),
        "status": "pending"
    },
    {
        "id": "rep-102",
        "title": "강남구 역삼역 앞 편도 3차선 대형 포트홀 방치",
        "category": "도로 시설물 파손",
        "authority": "강남구청 도로관리과",
        "coords": [37.5006, 127.0360],
        "address": "서울특별시 강남구 역삼동 736-1",
        "description": "강남구 역삼역 인근 삼거리 편도 3차선 도로 중 2차로 상에 직경 약 50cm, 깊이 10cm 크기의 대형 포트홀이 발생하여 통행 중인 차량들이 급차선 변경을 하거나 타이어 파손 사고가 발생하고 있습니다. 현장에 급아스콘 임시 복구 처방 및 근본적 포장 공사를 긴급 청원합니다.",
        "image": DEFAULT_PRESETS_GRAPHICS["pothole"],
        "timestamp": datetime.now().isoformat(),
        "status": "process"
    },
    {
        "id": "rep-103",
        "title": "마포구 연남동 주택가 이면도로 보안등 고장 소등",
        "category": "가로등/가로수 정비",
        "authority": "마포구청 도시디자인팀",
        "coords": [37.5615, 126.9248],
        "address": "서울특별시 마포구 연남동 228-4",
        "description": "연남동 먹자골목 및 주택가 밀집 지역 내의 골목길 보안등이 전구 수명 종료 또는 전기 단선으로 인해 완전히 작동하지 않아 일대 밤길 통행이 매우 위험하고 우범 지역화되고 있습니다. 안전한 보행을 위해 누전 수리 및 가로등 벌브 즉시 교체를 신청합니다.",
        "image": DEFAULT_PRESETS_GRAPHICS["streetlight"],
        "timestamp": datetime.now().isoformat(),
        "status": "done"
    }
]

PRESET_INFO = {
    "pothole": ("도로 시설물 파손", "강남구청 도로관리과", [37.5006, 127.0360], "서울특별시 강남구 역삼동 736-1", "차도 파손(포트홀) 즉각 보수 요청", "강남구 역삼역 인근 도로에 대형 포트홀이 발생하여 타이어 파손 및 2차 교통사고가 대단히 높으므로 신속한 임시 아스콘 복구를 요청합니다.", DEFAULT_PRESETS_GRAPHICS["pothole"]),
    "streetlight": ("가로등/가로수 정비", "마포구청 도시디자인팀", [37.5615, 126.9248], "서울특별시 마포구 연남동 228-4", "인도 보안등 고장 소등 조치 요청", "연남동 주택가 이면도로 가로등이 파손 또는 단선으로 완전히 소등되어 주민들 안전에 위해가 가해지고 있으니 전구 교체 바랍니다.", DEFAULT_PRESETS_GRAPHICS["streetlight"]),
    "parking": ("불법 주차/안전구역", "종로구청 교통지도과", [37.5724, 126.9856], "서울특별시 종로구 인사동 194-4", "소화전 주변 불법 주정차 벌금 조치 요청", "인사동 문화거리 소화전 주변 5m 이내에 차량이 무단 주정차하여 긴급 소방 활동을 방해하므로 견인 처리를 요청합니다.", DEFAULT_PRESETS_GRAPHICS["parking"])
}

# DB Helper
def load_reports():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(SEED_REPORTS, f, ensure_ascii=False, indent=4)
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return SEED_REPORTS

def save_reports(reports):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=4)

# Geocode helper
def get_coords_from_address(address):
    try:
        headers = {'User-Agent': 'SafetyReportGradio/1.0'}
        r = requests.get(f"https://nominatim.openstreetmap.org/search?format=json&q={address}&limit=1", headers=headers, timeout=5)
        if r.status_code == 200 and len(r.json()) > 0:
            data = r.json()[0]
            return [float(data["lat"]), float(data["lon"])], data.get("display_name", address)
    except:
        pass
    return [37.5665, 126.9780], address

# Gemini API call helper
def analyze_complaint_via_gemini(api_key, image_path, user_text):
    if not api_key:
        # Fallback simulation
        matched_preset = "pothole"
        txt = user_text.lower() if user_text else ""
        if any(x in txt for x in ["가로등", "보안등", "어둡", "불빛"]):
            matched_preset = "streetlight"
        elif any(x in txt for x in ["주차", "소화전", "차량"]):
            matched_preset = "parking"
        
        p_cat, p_auth, p_coords, p_addr, p_title, p_desc, p_img = PRESET_INFO[matched_preset]
        return {
            "title": f"[재구성] {p_title}",
            "category": p_cat,
            "authority": p_auth,
            "coords": p_coords,
            "address": p_addr,
            "content": f"제보자 추가 설명: '{user_text}'\n\n{p_desc}",
            "image": p_img
        }
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = """당신은 행정 민원 대필 및 공공 문제 해결사 AI 비서입니다. 사용자가 보낸 이미지와 메시지를 정확하게 파악하고, 관할 지자체 담당 부서에서 신속히 해결할 수 있도록 완성도 높은 행정 민원글 양식으로 대필해 주십시오.
        
        요구조건:
        1. 'title' (민원 제목), 'category' (예: 도로 시설물 파손, 불법 주차/안전구역, 가로등/가로수 정비, 교통사고/위험 등 중 택1), 'authority' (처리 담당부서), 'content' (육하원칙 본문)을 구성해야 합니다.
        2. 출력은 사족 없이 순수 JSON만 응답하세요:
        {
          "title": "[민원 제목]",
          "category": "[카테고리 분류]",
          "authority": "[관할 구청/지자체 처리 부서]",
          "content": "[상세 본문]"
        }"""
        
        contents = [prompt]
        if image_path:
            with open(image_path, "rb") as img_file:
                image_bytes = img_file.read()
            contents.append({
                "mime_type": "image/jpeg" if image_path.endswith((".jpg", ".jpeg")) else "image/png",
                "data": image_bytes
            })
            
        contents.append(f"사용자 제보 요청 메시지: {user_text if user_text else '이 상황에 대필 기안서를 적어줘.'}")
        
        response = model.generate_content(contents, generation_config={"response_mime_type": "application/json"})
        parsed_doc = json.loads(response.text)
        
        # Default coords
        parsed_doc["coords"] = [37.5665, 126.9780]
        parsed_doc["address"] = "서울특별시 중구 세종대로 110 (정확한 위치를 직접 입력/검색해 주세요)"
        
        if image_path:
            with open(image_path, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode('utf-8')
                parsed_doc["image"] = f"data:image/png;base64,{encoded}"
        else:
            parsed_doc["image"] = DEFAULT_PRESETS_GRAPHICS["pothole"]
            
        return parsed_doc
    except Exception as e:
        return {"error": str(e)}

# Render Folium Map to HTML string
def build_community_map_html(selected_category="전체보기"):
    reports = load_reports()
    
    # Base location
    center = [37.54, 126.98]
    m = folium.Map(location=center, zoom_start=11)
    
    color_map = {
        "교통사고/위험": "red",
        "도로 시설물 파손": "orange",
        "가로등/가로수 정비": "blue",
        "불법 주차/안전구역": "purple"
    }
    
    filtered = reports if selected_category == "전체보기" else [r for r in reports if r["category"] == selected_category]
    
    for rep in filtered:
        marker_color = color_map.get(rep["category"], "red")
        
        popup_html = f"""
            <div style="font-family:sans-serif; width:220px; color:#fff; background:#0f172a; padding:10px; border-radius:8px; font-size: 13px;">
                <img src="{rep['image']}" style="width:100%; height:110px; object-fit:cover; border-radius:4px; margin-bottom: 6px;" />
                <h4 style="margin:4px 0 2px; font-weight:bold; font-size:14px; color:#2dd4bf;">{rep['title']}</h4>
                <p style="font-size:12px; color:#94a3b8; margin:0 0 6px;">📍 {rep['address']}</p>
                <p style="font-size:11px; color:#cbd5e1; line-height:1.4; margin:0;">{rep['description'][:60]}...</p>
                <div style="margin-top:8px; font-size:11px; font-weight:bold; color:#f59e0b;">상태: {rep.get('status', 'pending')}</div>
            </div>
        """
        iframe = folium.IFrame(popup_html, width=240, height=230)
        popup = folium.Popup(iframe, max_width=250)
        icon = folium.Icon(color=marker_color, icon="info-sign")
        folium.Marker(rep["coords"], popup=popup, icon=icon).add_to(m)

        
    return m._repr_html_()

# Build Feed HTML list
def build_feed_html(selected_category="전체보기"):
    reports = load_reports()
    filtered = reports if selected_category == "전체보기" else [r for r in reports if r["category"] == selected_category]
    
    html = "<div style='display:flex; flex-direction:column; gap:12px; max-height:480px; overflow-y:auto; padding:10px;'>"
    if not filtered:
        html += "<p style='color:#94a3b8; text-align:center;'>제보가 없습니다.</p>"
        
    for rep in filtered:
        badge_color = "rgba(239, 68, 68, 0.15)"
        text_color = "#f87171"
        if "도로" in rep["category"]:
            badge_color = "rgba(245, 158, 11, 0.15)"
            text_color = "#f59e0b"
        elif "가로등" in rep["category"]:
            badge_color = "rgba(6, 182, 212, 0.15)"
            text_color = "#06b6d4"
        elif "주차" in rep["category"]:
            badge_color = "rgba(168, 85, 247, 0.15)"
            text_color = "#c084fc"
            
        html += f"""
        <div style="background:rgba(22, 29, 49, 0.8); border:1px solid rgba(255,255,255,0.08); border-radius:10px; padding:14px; color:#f8fafc;">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                <span style="background:{badge_color}; color:{text_color}; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:bold;">{rep['category']}</span>
                <span style="font-size:11px; color:#f59e0b;">{rep.get('status', 'pending').upper()}</span>
            </div>
            <h4 style="margin:4px 0 6px; font-size:14px; font-weight:bold;">{rep['title']}</h4>
            <p style="margin:0 0 6px; font-size:12px; color:#94a3b8;">📍 {rep['address']}</p>
            <p style="margin:0; font-size:12px; color:#cbd5e1; line-height:1.4;">{rep['description'][:100]}...</p>
            <div style="font-size:10px; color:#6b7280; margin-top:8px; text-align:right;">제보시간: {rep['timestamp'][:16].replace('T', ' ')}</div>
        </div>
        """
    html += "</div>"
    return html

# App Theme Stylesheet
theme_css = """
body {
    background-color: #090d16 !important;
    color: #f8fafc !important;
}
.gradio-container {
    background-color: #090d16 !important;
    max-width: 1200px !important;
    margin: 0 auto !important;
    font-family: 'Inter', sans-serif !important;
}
.tabs {
    border-bottom: 1px solid rgba(255, 255, 255, 0.1) !important;
}
.tabitem {
    background-color: #090d16 !important;
}
button.primary {
    background: linear-gradient(135deg, #14b8a6, #06b6d4) !important;
    color: white !important;
    border: none !important;
}
button.primary:hover {
    filter: brightness(1.1) !important;
}
input, textarea, select {
    background-color: rgba(22, 29, 49, 0.7) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    color: #f8fafc !important;
}
.feedback-box {
    background-color: rgba(22, 29, 49, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 12px;
    padding: 16px;
}
"""

# Global State
temp_draft = {}

with gr.Blocks(css=theme_css, title="민원 해결사 AI - 실시간 시민 제보 공유 지도") as demo:
    gr.HTML("""
        <div style="text-align: center; margin-bottom: 24px; padding-top: 10px;">
            <h1 style="color: #2dd4bf; font-size: 2.2rem; font-weight: 800; margin-bottom: 6px;">🚨 민원 해결사 AI</h1>
            <p style="color: #94a3b8; font-size: 1rem;">원터치 안전신문고 기안 및 실시간 시민 공유 지도</p>
        </div>
    """)
    
    with gr.Tabs():
        # --- TAB 1: AI COMPLAINT MAKER ---
        with gr.TabItem("📋 AI 민원 대필기"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 📸 사진 제보 및 상황 설명")
                    api_key = gr.Textbox(label="🔑 Gemini API Key 설정 (공백 시 시뮬레이션 모드)", type="password", placeholder="AI 분석용 Gemini API 키 입력")
                    image_in = gr.Image(label="현장 이미지 업로드 (드래그 앤 드롭)", type="filepath")
                    text_in = gr.Textbox(label="상황 설명", placeholder="예: '길거리에 싱크홀이 뚫려있어서 차들이 피해가요'")
                    
                    with gr.Row():
                        btn_preset1 = gr.Button("💥 포트홀 시나리오", size="sm")
                        btn_preset2 = gr.Button("💡 가로등 고장 시나리오", size="sm")
                        btn_preset3 = gr.Button("🚗 불법주차 시나리오", size="sm")
                        
                    btn_submit = gr.Button("📝 AI 민원 대필 신청", variant="primary")
                    
                with gr.Column(scale=1):
                    gr.Markdown("### 📄 생성된 민원 신고서 검토")
                    out_title = gr.Textbox(label="■ 민원 제목")
                    out_category = gr.Textbox(label="■ 카테고리")
                    out_authority = gr.Textbox(label="■ 관할 담당 기관")
                    
                    with gr.Row():
                        out_address = gr.Textbox(label="■ 발생 주소", scale=3)
                        btn_geocode = gr.Button("🔍 위치 검색", scale=1)
                        
                    out_content = gr.TextArea(label="■ 민원 상세 내용 (육하원칙 공적 문서 포맷)", lines=8)
                    out_image_url = gr.State("")
                    out_coords = gr.State([37.5665, 126.9780])
                    
                    with gr.Row():
                        btn_download = gr.Button("💾 텍스트 다운로드")
                        btn_safety = gr.Button("🔗 안전신문고 바로가기", variant="secondary")
                        btn_map_register = gr.Button("🗺️ 실시간 공유 지도 등록", variant="primary")
                        
        # --- TAB 2: REALTIME MAP DASHBOARD ---
        with gr.TabItem("🗺️ 실시간 시민 공유 지도"):
            with gr.Row():
                with gr.Column(scale=2):
                    gr.Markdown("### 🗺️ 시민 제보 위치 상황판")
                    map_view = gr.HTML(value=build_community_map_html())
                    
                with gr.Column(scale=1):
                    gr.Markdown("### 🔔 실시간 제보 피드")
                    filter_cat = gr.Dropdown(choices=["전체보기", "교통사고/위험", "도로 시설물 파손", "가로등/가로수 정비", "불법 주차/안전구역"], value="전체보기", label="🎯 카테고리 필터")
                    feed_view = gr.HTML(value=build_feed_html())
                    btn_refresh = gr.Button("🔄 지도/피드 새로고침")

    # Define Event Handlers
    
    # Preset triggers
    def load_preset(scenario):
        p_cat, p_auth, p_coords, p_addr, p_title, p_desc, p_img = PRESET_INFO[scenario]
        return p_title, p_cat, p_auth, p_addr, p_desc, p_img, p_coords
        
    btn_preset1.click(lambda: load_preset("pothole"), outputs=[out_title, out_category, out_authority, out_address, out_content, out_image_url, out_coords])
    btn_preset2.click(lambda: load_preset("streetlight"), outputs=[out_title, out_category, out_authority, out_address, out_content, out_image_url, out_coords])
    btn_preset3.click(lambda: load_preset("parking"), outputs=[out_title, out_category, out_authority, out_address, out_content, out_image_url, out_coords])

    # AI generation trigger
    def run_ai(key, img, text):
        res = analyze_complaint_via_gemini(key, img, text)
        if "error" in res:
            gr.Warning(f"AI 호출 중 에러 발생: {res['error']}")
            return "", "", "", "", "", "", [37.5665, 126.9780]
        return res["title"], res["category"], res["authority"], res["address"], res["content"], res["image"], res["coords"]
        
    btn_submit.click(run_ai, inputs=[api_key, image_in, text_in], outputs=[out_title, out_category, out_authority, out_address, out_content, out_image_url, out_coords])

    # Geocoding search trigger
    def search_address(addr):
        coords, matched_addr = get_coords_from_address(addr)
        return matched_addr, coords
        
    btn_geocode.click(search_address, inputs=[out_address], outputs=[out_address, out_coords])

    # Map Registration trigger
    def register_report(title, cat, auth, addr, content, img_b64, coords):
        if not title:
            gr.Warning("작성된 민원이 없습니다. 대필을 먼저 진행해 주세요.")
            return build_community_map_html(), build_feed_html()
            
        reports = load_reports()
        new_report = {
            "id": f"rep-{int(datetime.now().timestamp())}",
            "title": title,
            "category": cat,
            "authority": auth,
            "coords": coords,
            "address": addr,
            "description": content,
            "image": img_b64 if img_b64 else DEFAULT_PRESETS_GRAPHICS["pothole"],
            "timestamp": datetime.now().isoformat(),
            "status": "pending"
        }
        reports.insert(0, new_report)
        save_reports(reports)
        gr.Info("실시간 시민 공유 지도에 성공적으로 등록되었습니다!")
        return build_community_map_html(), build_feed_html()
        
    btn_map_register.click(register_report, inputs=[out_title, out_category, out_authority, out_address, out_content, out_image_url, out_coords], outputs=[map_view, feed_view])

    # Refresh triggers
    def refresh_dashboard(category):
        return build_community_map_html(category), build_feed_html(category)
        
    filter_cat.change(refresh_dashboard, inputs=[filter_cat], outputs=[map_view, feed_view])
    btn_refresh.click(refresh_dashboard, inputs=[filter_cat], outputs=[map_view, feed_view])

    # External links & files
    btn_safety.click(fn=None, js="window.open('https://www.safetyreport.go.kr', '_blank')")
    
    # Download helper
    def download_text(title, addr, content):
        if not title:
            return None
        text = f"■ 제목: {title}\n■ 장소: {addr}\n■ 내용:\n{content}"
        # save temp text file
        filepath = "minwon_report.txt"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text)
        return filepath
        
    # gr.File component invisible helper to download
    file_downloader = gr.File(label="다운로드 파일", visible=False)
    btn_download.click(download_text, inputs=[out_title, out_address, out_content], outputs=[file_downloader])
    # When file is generated, make it visible to download
    def show_downloader(file):
        if file:
            return gr.update(visible=True)
        return gr.update(visible=False)
    file_downloader.change(show_downloader, inputs=[file_downloader], outputs=[file_downloader])

# Launch demo
if __name__ == "__main__":
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)

