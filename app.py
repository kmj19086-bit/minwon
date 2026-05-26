import streamlit as st
import folium
from streamlit_folium import st_folium
import google.generativeai as genai
import json
import os
import requests
from datetime import datetime
import base64

# Set Page Config
st.set_page_config(
    page_title="민원 해결사 AI - 실시간 공유 지도",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling via CSS injection
def inject_custom_css():
    st.markdown("""
        <style>
        /* Dark Slate & Teal Theme Overrides */
        .stApp {
            background-color: #090d16;
            background-image: 
                radial-gradient(at 0% 0%, rgba(20, 184, 166, 0.06) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(6, 182, 212, 0.06) 0px, transparent 50%);
            color: #f8fafc;
        }
        
        /* Glassmorphism containers */
        div[data-testid="stVerticalBlock"] > div {
            border-radius: 12px;
        }
        
        /* Custom card styling */
        .feed-card-box {
            background-color: rgba(22, 29, 49, 0.7);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            cursor: pointer;
            transition: all 0.2s ease;
        }
        .feed-card-box:hover {
            border-color: #14b8a6;
            background-color: rgba(20, 184, 166, 0.03);
            transform: translateY(-2px);
        }
        
        /* Accents */
        .accent-text {
            color: #2dd4bf;
            font-weight: 700;
        }
        
        /* Badge styling */
        .custom-badge {
            display: inline-block;
            padding: 2px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: bold;
            margin-right: 6px;
        }
        .badge-pothole { background-color: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }
        .badge-accident { background-color: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
        .badge-light { background-color: rgba(6, 182, 212, 0.15); color: #06b6d4; border: 1px solid rgba(6, 182, 212, 0.3); }
        .badge-parking { background-color: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }
        
        .status-badge {
            float: right;
            font-size: 0.72rem;
            font-weight: bold;
        }
        .status-pending { color: #f59e0b; }
        .status-process { color: #06b6d4; }
        .status-done { color: #34d399; }
        
        /* Map wrapper */
        .map-wrapper {
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            overflow: hidden;
        }
        </style>
    """, unsafe_allow_html=True)

# File Paths
DB_FILE = "reports.json"

# Seeding dynamic preset illustrative graphics
DEFAULT_PRESETS_GRAPHICS = {
    "pothole": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjNGI1NTYzIi8+PHBhdGggZD0iTTUwIDEyMCBRODAgMTUwIDEyMCAxMjAgVDIwMCAxMzAgVDI1MCAxMDBRMTgwIDYwIDE0MCAxMDBUNTAgMTIwIiBmaWxsPSIjMWYyOTM3Ii8+PGNpcmNsZSBjeD0iMTIwIiBjeT0iMTE1IiByPSIxNSIgZmlsbD0iIzExMTgyNyIvPjxjaXJjbGUgY3g9IjE3MCIgY3k9IjExMCIgcj0iMTAiIGZpbGw9IiMxMTE4MjciLz48dGV4dCB4PSIyMCIgeT0iNDAiIGZpbGw9IndoaXRlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9ImJvbGQiIGZvbnQtc2l6ZT0iMTQiPkRFRVAgUk9BRCBQT1RIT0xEPC90ZXh0Pjwvc3ZnPg==",
    "streetlight": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMTExODI3Ii8+PGxpbmUgeDE9IjE1MCIgeTE9IjUwIiB4Mj0iMTUwIiB5Mj0iMTkwIiBzdHJva2U9IiM2YjcyODAiIHN0cm9rZS13aWR0aD0iNiIvPjxjaXJjbGUgY3g9IjE1MCIgY3k9IjUwIiByPSIxMiIgZmlsbD0iI2VhYjMwOCIgb3BhY2l0eT0iMC4zIi8+PGNpcmNsZSBjeD0iMTUwIiBjeT0iNTAiIHI9IjYiIGZpbGw9IiM5Y2EzYWYiLz48dGV4dCB4PSIyMCIgeT0iNDAiIGZpbGw9IiNmODcxNzEiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iYm9sZCIgZm9udC1zaXplPSIxNCI+QlJPS0VOIFNUUkVFVExJR0hUPC90ZXh0Pjwvc3ZnPg==",
    "parking": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjZmVmMmYyIi8+PHJlY3QgeD0iODAiIHk9IjcwIiB3aWR0aD0iMTQwIiBoZWlnaHQ9IjcwIiByeD0iMTAiIGZpbGw9IiNlZjQ0NDQiLz48Y2lyY2xlIGN4PSIxMTAiIGN5PSIxNDAiIHI9IjE4IiBmaWxsPSIjMWYyOTM3Ii8+PGNpcmNsZSBjeD0iMTkwIiBjeT0iMTQwIiByPSIxOCIgZmlsbD0iIzFmMjkzNyIvPjxjaXJjbGUgY3g9IjE1MCIgY3k9IjEwMCIgcj0iMzAiIHN0cm9rZT0iI2I5MWMxYyIgc3Ryb2tlLXdpZHRoPSI4IiBmaWxsPSJub25lIi8+PHRleHQgeD0iMjAiIHk9IjQwIiBmaWxsPSIjYjkxYzFjIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC13ZWlnaHQ9ImJvbGQiIGZvbnQtc2l6ZT0iMTQiPklMTEVHQUwgUEFSS0lORzwvdGV4dD48L3N2Zz4=",
    "accident": "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjAwIj48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSIjMWUyOTNiIi8+PHBhdGggZD0iTTQwIDE0MCBMMTMwIDExMCBMMTgwIDEyMCBMMjcwIDE0MCIgc3Ryb2tlPSIjNGI1NTYzIiBzdHJva2Utd2lkdGg9IjgiIGZpbGw9Im5vbmUiLz48cmVjdCB4PSI2MCIsInk9IjkwIiB3aWR0aD0iNjAiIGhlaWdodD0iMzAiIGZpbGw9IiNlZjQ0NDQiIHRyYW5zZm9ybT0icm90YXRlKC0xMCwgNjAsIDkwKSIvPjxyZWN0IHg9IjEyMCIgeT0iODUiIHdpZHRoPSI2MCIgaGVpZ2h0PSIzMCIgZmlsbD0iIzNiODJmNiIgdHJhbnNmb3JtPSJyb3RhdGUoNSwgMTIwLCA4NSkiLz48Y2lyY2xlIGN4PSI3MCIgY3k9IjExNSIgcj0iMTAiIGZpbGw9ImJsYWNrIi8+PGNpcmNsZSBjeD0iMTcwIiBjeT0iMTE1IiByPSIxMCIgZmlsbD0iYmxhY2siLz48dGV4dCB4PSIyMCIgeT0iNDAiIGZpbGw9IiNmODcxNzEiIGZvbnQtZmFtaWx5PSJzYW5zLXNlcmlmIiBmb250LXdlaWdodD0iYm9sZCIgZm9udC1zaXplPSIxNCI+M19DQVJfQ09MTElTSU9OX09OX0hJR0hXQVk8L3RleHQ+PC9zdmc+"
}

# Seed Data (simulating database records)
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
    },
    {
        "id": "rep-104",
        "title": "종로구 인사동 문화거리 소화전 앞 차량 상습 불법 주정차",
        "category": "불법 주차/안전구역",
        "authority": "종로구청 교통지도과",
        "coords": [37.5724, 126.9856],
        "address": "서울특별시 종로구 인사동 194-4",
        "description": "인사동 상가 진입로 지상식 소화전 소방 시설의 반경 5m 이내 절대 주정차 금지 구간에 대형 SUV 차량이 상습 무단 주정차하여 통행 곤란 및 화재 대처 방해를 초래하고 있습니다. 지자체 상시 계도 조치 및 견인 단속 딱지 부과를 요청합니다.",
        "image": DEFAULT_PRESETS_GRAPHICS["parking"],
        "timestamp": datetime.now().isoformat(),
        "status": "done"
    }
]

# Presets Data for simulation fallback
PRESET_INFO = {
    "pothole": ("도로 시설물 파손", "강남구청 도로관리과", [37.5006, 127.0360], "서울특별시 강남구 역삼동 736-1", "차도 파손(포트홀) 즉각 보수 요청", "강남구 역삼역 인근 도로에 대형 포트홀이 발생하여 타이어 파손 및 2차 교통사고가 대단히 높으므로 신속한 임시 아스콘 복구를 요청합니다.", DEFAULT_PRESETS_GRAPHICS["pothole"]),
    "streetlight": ("가로등/가로수 정비", "마포구청 도시디자인팀", [37.5615, 126.9248], "서울특별시 마포구 연남동 228-4", "인도 보안등 고장 소등 조치 요청", "연남동 주택가 이면도로 가로등이 파손 또는 단선으로 완전히 소등되어 주민들 안전에 위해가 가해지고 있으니 전구 교체 바랍니다.", DEFAULT_PRESETS_GRAPHICS["streetlight"]),
    "parking": ("불법 주차/안전구역", "종로구청 교통지도과", [37.5724, 126.9856], "서울특별시 종로구 인사동 194-4", "소화전 주변 불법 주정차 벌금 조치 요청", "인사동 문화거리 소화전 주변 5m 이내에 차량이 무단 주정차하여 긴급 소방 활동을 방해하므로 견인 처리를 요청합니다.", DEFAULT_PRESETS_GRAPHICS["parking"])
}

# Database Loading/Saving
def init_database():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(SEED_REPORTS, f, ensure_ascii=False, indent=4)

def load_reports():
    init_database()
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return SEED_REPORTS

def save_reports(reports):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(reports, f, ensure_ascii=False, indent=4)

# Load database into Session State
if "reports" not in st.session_state:
    st.session_state.reports = load_reports()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "ai", "content": "안녕하세요! 동네의 위험 요소나 안전 불편 현장 사진을 올리시고 간단한 한 마디만 적어주세요. AI가 신속하고 완벽하게 육하원칙 공적 민원서로 변환해 드립니다. 아래의 예제 시나리오 버튼을 눌러 바로 테스트해보실 수도 있습니다."}
    ]

if "draft" not in st.session_state:
    st.session_state.draft = None

if "community_center" not in st.session_state:
    st.session_state.community_center = [37.54, 126.98]

if "community_zoom" not in st.session_state:
    st.session_state.community_zoom = 11

inject_custom_css()

# API Reverse Geocoding via Nominatim Open API
def get_address_from_coords(lat, lon):
    try:
        headers = {'User-Agent': 'SafetyReportStreamlit/1.0'}
        r = requests.get(f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1", headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            display_name = data.get("display_name", "")
            parts = [p.strip() for p in display_name.split(',')]
            parts.reverse()
            # filter out Country (index 0)
            address = " ".join(parts[1:])
            return address if address else display_name
    except Exception as e:
        pass
    return f"서울특별시 중구 세종대로 110 (좌표: {lat:.4f}, {lon:.4f})"

# Gemini API call helper
def analyze_complaint_via_gemini(api_key, image_bytes, image_type, user_text):
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        prompt = """당신은 행정 민원 대필 및 공공 문제 해결사 AI 비서입니다. 사용자가 보낸 이미지와 메시지를 정확하게 파악하고, 관할 지자체 담당 부서에서 신속히 해결할 수 있도록 완성도 높은 행정 민원글 양식으로 대필해 주십시오.

요구조건:
1. '민원 제목', '카테고리' (예: 도로 시설물 파손, 불법 주차/안전구역, 가로등/가로수 정비, 교통사고/위험, 쓰레기 방치 등 중 택1), '처리 담당부서' (예: 도로관리과, 교통지도과, 자원순환과 등), '상세 본문'을 구성해야 합니다.
2. 상세 본문은 육하원칙(언제, 어디서, 누가/무엇을, 어떻게, 왜, 대안요청)이 명확히 담기도록 정중하고 공적인 문서 톤앤매너로 성안해 주세요.
3. 출력은 반드시 아래의 JSON 포맷 형식을 유지해야 합니다. 다른 사족을 붙이지 말고 순수한 JSON만 응답해 주세요.

출력 JSON 스펙:
{
  "title": "[민원 제목 입력]",
  "category": "[카테고리 분류]",
  "authority": "[관할 구청/지자체 처리 부서]",
  "content": "[육하원칙 상세 본문 내용]"
}"""
        
        contents = [prompt]
        if image_bytes:
            contents.append({
                "mime_type": image_type,
                "data": image_bytes
            })
            
        contents.append(f"사용자 제보 요청 메시지: {user_text if user_text else '이 상황에 대필 기안서를 적어줘.'}")
        
        response = model.generate_content(contents, generation_config={"response_mime_type": "application/json"})
        parsed_doc = json.loads(response.text)
        return parsed_doc
    except Exception as e:
        st.error(f"Gemini API 에러: {e}")
        return None

# Sidebar Configuration
st.sidebar.markdown("# 🚨 민원 해결사 <span class='accent-text'>AI</span>", unsafe_allow_html=True)
st.sidebar.caption("원터치 안전신문고 기안 & 실시간 공유 맵")
st.sidebar.markdown("---")

api_key_input = st.sidebar.text_input("🔑 Gemini API Key 설정", type="password", help="입력 시 실제 이미지 분석 모드로 전환되며, 미입력 시 시뮬레이션 모드로 작동합니다.")
if api_key_input:
    st.sidebar.success("Gemini API 모드 활성화됨")
else:
    st.sidebar.warning("시뮬레이션 모드로 실행 중")

st.sidebar.markdown("---")
if st.sidebar.button("🗑️ 대화 내역 초기화", use_container_width=True):
    st.session_state.messages = [
        {"role": "ai", "content": "안녕하세요! 동네의 위험 요소나 안전 불편 현장 사진을 올리시고 간단한 한 마디만 적어주세요. AI가 신속하고 완벽하게 육하원칙 공적 민원서로 변환해 드립니다. 아래의 예제 시나리오 버튼을 눌러 바로 테스트해보실 수도 있습니다."}
    ]
    st.session_state.draft = None
    st.rerun()

if st.sidebar.button("🔄 공유 지도 전체 리셋", use_container_width=True):
    st.session_state.reports = SEED_REPORTS.copy() # fallback to raw seed
    save_reports(st.session_state.reports)
    st.sidebar.success("지도가 초기값으로 리셋되었습니다.")
    st.rerun()

# Tabs
tab1, tab2 = st.tabs(["📋 AI 민원 대필기", "🗺️ 실시간 시민 공유 지도"])

# --- TAB 1: AI COMPLAINT GENERATOR ---
with tab1:
    col1, col2 = st.columns([1, 1])
    
    # Left Column: Chat Area
    with col1:
        st.subheader("AI 접수 도우미")
        
        # Render Chat History
        chat_container = st.container(height=450)
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    if "image" in msg:
                        st.image(msg["image"], width=250)
                    st.write(msg["content"])
        
        # Preset buttons for testing
        st.caption("⚙️ 체험용 가상 시나리오 클릭:")
        pre_col1, pre_col2, pre_col3 = st.columns(3)
        
        preset_clicked = None
        if pre_col1.button("💥 도로 포트홀", use_container_width=True):
            preset_clicked = "pothole"
        if pre_col2.button("💡 가로등 고장", use_container_width=True):
            preset_clicked = "streetlight"
        if pre_col3.button("🚗 소화전 불법주차", use_container_width=True):
            preset_clicked = "parking"
            
        if preset_clicked:
            p_cat, p_auth, p_coords, p_addr, p_title, p_desc, p_img = PRESET_INFO[preset_clicked]
            
            # Update Chat
            st.session_state.messages.append({"role": "user", "content": f"[샘플 시나리오 작동] {p_title} 현장 분석 및 대필을 시작합니다.", "image": p_img})
            st.session_state.messages.append({"role": "ai", "content": "현장 분석 완료 및 민원 작성이 완료되었습니다! 우측 결과창을 확인하세요."})
            
            st.session_state.draft = {
                "title": p_title,
                "category": p_cat,
                "authority": p_auth,
                "coords": p_coords,
                "address": p_addr,
                "description": p_desc,
                "image": p_img
            }
            st.rerun()

        # Input elements
        uploaded_image = st.file_uploader("📸 현장 이미지 업로드 (드래그 앤 드롭 지원)", type=["png", "jpg", "jpeg"])
        user_input = st.chat_input("여기에 상황 설명을 간단히 남겨주세요 (예: '도로에 구멍이 뚫려있어')")
        
        if user_input:
            image_data = None
            image_b64 = None
            if uploaded_image:
                image_bytes = uploaded_image.getvalue()
                image_type = uploaded_image.type
                image_b64 = f"data:{image_type};base64," + base64.b64encode(image_bytes).decode('utf-8')
                st.session_state.messages.append({"role": "user", "content": user_input, "image": image_b64})
            else:
                st.session_state.messages.append({"role": "user", "content": user_input})
                
            # Perform API call / fallback
            with st.spinner("AI가 현장 데이터를 심층 분석하여 기안서를 작성하고 있습니다..."):
                if api_key_input and uploaded_image:
                    res_json = analyze_complaint_via_gemini(api_key_input, uploaded_image.getvalue(), uploaded_image.type, user_input)
                    if res_json:
                        st.session_state.draft = {
                            "title": res_json.get("title", "지역 생활 민원 개선 청원"),
                            "category": res_json.get("category", "기타 안전/시설 개선"),
                            "authority": res_json.get("authority", "지자체 종합민원과"),
                            "coords": [37.5665, 126.9780],
                            "address": "서울특별시 중구 세종대로 110 (지도를 클릭하여 정확한 장소를 선택해 주세요)",
                            "description": res_json.get("content", ""),
                            "image": image_b64 if image_b64 else DEFAULT_PRESETS_GRAPHICS["pothole"]
                        }
                else:
                    # Simulation Mode fallback
                    # Check keywords
                    matched_preset = "pothole" # default fallback
                    txt = user_input.lower()
                    if any(x in txt for x in ["가로등", "보안등", "어둡", "불빛"]):
                        matched_preset = "streetlight"
                    elif any(x in txt for x in ["주차", "소화전", "차량"]):
                        matched_preset = "parking"
                    
                    p_cat, p_auth, p_coords, p_addr, p_title, p_desc, p_img = PRESET_INFO[matched_preset]
                    
                    st.session_state.draft = {
                        "title": f"[재구성] {p_title}",
                        "category": p_cat,
                        "authority": p_auth,
                        "coords": p_coords,
                        "address": f"제보 구역 인근: {p_addr}",
                        "description": f"제보자 추가 입력내용: '{user_input}'\n\n{p_desc}",
                        "image": image_b64 if image_b64 else p_img
                    }
            
            st.session_state.messages.append({"role": "ai", "content": "작성 완료! 우측 신고서의 세부 내용을 최종 검토하고 주소를 지도에서 선택해 주세요."})
            st.rerun()

    # Right Column: Generated Document
    with col2:
        st.subheader("민원 신고서 작성 결과")
        
        if not st.session_state.draft:
            st.info("왼쪽 대화 창에서 제보를 접수해 주시면 여기에 민원 신고서가 자동으로 생성됩니다.")
        else:
            draft = st.session_state.draft
            
            # Input Fields
            st.markdown(f"**카테고리**: `{draft['category']}` | **처리기관**: `{draft['authority']}`")
            
            title_field = st.text_input("■ 민원 제목", value=draft["title"])
            address_field = st.text_input("■ 발생 장소 (아래 지도 클릭으로 자동 설정)", value=draft["address"])
            
            # Leaflet Map setup
            st.markdown("**📍 지도에서 상세 사고 위치 클릭**")
            m_editor = folium.Map(location=draft["coords"], zoom_start=16)
            folium.Marker(draft["coords"], popup="신고 지점").addTo(m_editor)
            
            map_data = st_folium(m_editor, height=220, use_container_width=True, key="editor_map")
            
            # Handle map click to update coordinates
            if map_data and map_data.get("last_clicked"):
                clicked_coords = [map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"]]
                if clicked_coords != draft["coords"]:
                    with st.spinner("새로운 주소 정보를 받아오고 있습니다..."):
                        new_address = get_address_from_coords(clicked_coords[0], clicked_coords[1])
                        st.session_state.draft["coords"] = clicked_coords
                        st.session_state.draft["address"] = new_address
                    st.rerun()

            content_field = st.text_area("■ 민원 내용 (육하원칙 포맷)", value=draft["description"], height=180)
            
            # Actions
            act_col1, act_col2, act_col3 = st.columns(3)
            
            # Copy to Clipboard representation
            full_text = f"■ 제목: {title_field}\n■ 장소: {address_field}\n■ 내용:\n{content_field}"
            act_col1.download_button("💾 메모장 다운", data=full_text, file_name=f"신청서_{title_field}.txt", mime="text/plain", use_container_width=True)
            
            # Direct link to Safety Report
            act_col2.markdown(f'<a href="https://www.safetyreport.go.kr" target="_blank" style="text-decoration:none;"><button style="width:100%; border:1px solid #14b8a6; background-color:transparent; color:#2dd4bf; padding:6px; border-radius:4px; font-weight:bold; cursor:pointer;">🔗 안전신문고 접수</button></a>', unsafe_allow_html=True)
            
            # Register in Community Shared Map
            if act_col3.button("🗺️ 공유 지도 등록", type="primary", use_container_width=True):
                new_report = {
                    "id": f"rep-{int(datetime.now().timestamp())}",
                    "title": title_field,
                    "category": draft["category"],
                    "authority": draft["authority"],
                    "coords": draft["coords"],
                    "address": address_field,
                    "description": content_field,
                    "image": draft["image"],
                    "timestamp": datetime.now().isoformat(),
                    "status": "pending"
                }
                
                # Append to list and save
                st.session_state.reports.insert(0, new_report)
                save_reports(st.session_state.reports)
                
                # Setup community view focus
                st.session_state.community_center = draft["coords"]
                st.session_state.community_zoom = 15
                
                st.session_state.draft = None
                st.toast("실시간 시민 공유 지도에 성공적으로 등록되었습니다!", icon="🗺️")
                
                # Delay for a brief moment then rerun to show in Tab 2
                st.rerun()

# --- TAB 2: REALTIME COMMUNITY MAP ---
with tab2:
    st.subheader("실시간 시민 제보 공유 지도 (종합 상황판)")
    
    # Grid Layout: Left Map, Right Feed Sidebar
    com_col1, com_col2 = st.columns([2, 1])
    
    # Load list
    reports = st.session_state.reports
    
    with com_col2:
        st.markdown("### 🔔 최근 시민 실시간 제보 피드")
        
        # Category Filter
        categories = ["전체보기", "교통사고/위험", "도로 시설물 파손", "가로등/가로수 정비", "불법 주차/안전구역"]
        selected_category = st.selectbox("🎯 카테고리 필터링", categories)
        
        # Filter reports
        if selected_category == "전체보기":
            filtered_reports = reports
        else:
            filtered_reports = [r for r in reports if r["category"] == selected_category]
            
        st.caption(f"검색 결과: 총 {len(filtered_reports)}건")
        
        # Render feed timeline cards
        feed_container = st.container(height=420)
        with feed_container:
            for rep in filtered_reports:
                # Determine tag class
                badge_type = "badge-accident"
                if "도로" in rep["category"]: badge_type = "badge-pothole"
                elif "가로등" in rep["category"]: badge_type = "badge-light"
                elif "주차" in rep["category"]: badge_type = "badge-parking"
                
                status_korean = "접수 대기"
                status_class = "status-pending"
                if rep["status"] == "process":
                    status_korean = "처리 중"
                    status_class = "status-process"
                elif rep["status"] == "done":
                    status_korean = "해결 완료"
                    status_class = "status-done"
                
                # Card HTML structure
                card_html = f"""
                    <div class="feed-card-box">
                        <span class="custom-badge {badge_type}">{rep['category']}</span>
                        <span class="status-badge {status_class}">{status_korean}</span>
                        <h4 style="margin: 8px 0 4px; font-size:0.92rem;">{rep['title']}</h4>
                        <p style="font-size:0.75rem; color:#94a3b8; margin-bottom: 8px;">📍 {rep['address']}</p>
                    </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                # Interaction buttons inside Streamlit column structure
                card_col1, card_col2 = st.columns([3, 1])
                card_col1.caption(f"제보시각: {rep['timestamp'][:16].replace('T', ' ')}")
                
                if card_col2.button("🔍 보기", key=f"focus-{rep['id']}", size="small"):
                    st.session_state.community_center = rep["coords"]
                    st.session_state.community_zoom = 15
                    st.rerun()

    with com_col1:
        st.markdown("**🗺️ 지도 클릭 또는 사이드바 [보기] 버튼으로 줌/이동 가능**")
        
        # Render Leaflet Map
        m_community = folium.Map(
            location=st.session_state.community_center, 
            zoom_start=st.session_state.community_zoom
        )
        
        # Match pin colors
        color_map = {
            "교통사고/위험": "red",
            "도로 시설물 파손": "orange",
            "가로등/가로수 정비": "blue",
            "불법 주차/안전구역": "purple"
        }
        
        # Filter map pins based on category
        map_reports = filtered_reports
        
        for rep in map_reports:
            marker_color = color_map.get(rep["category"], "red")
            
            # HTML Popup
            popup_html = f"""
                <div style="font-family:'Outfit',sans-serif; width:220px; color:#fff; background:#0f172a; padding:6px; border-radius:8px;">
                    <img src="{rep['image']}" style="width:100%; height:110px; object-fit:cover; border-radius:4px;" />
                    <h4 style="margin:6px 0 2px; font-size:0.88rem; font-weight:bold;">{rep['title']}</h4>
                    <p style="font-size:0.75rem; color:#94a3b8; margin:0 0 6px;">📍 {rep['address']}</p>
                    <p style="font-size:0.7rem; color:#cbd5e1; line-height:1.3;">{rep['description'][:60]}...</p>
                </div>
            """
            
            iframe = folium.IFrame(popup_html, width=240, height=230)
            popup = folium.Popup(iframe, max_width=250)
            
            icon = folium.Icon(color=marker_color, icon="info-sign")
            folium.Marker(rep["coords"], popup=popup, icon=icon).addTo(m_community)
            
        import streamlit.components.v1 as components
        components.html(m_community._repr_html_(), height=450)

