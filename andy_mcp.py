import json
import random
from pathlib import Path
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from fastmcp import FastMCP

from hotdeal.ruliweb import get_ruliweb_hotdeal

mcp = FastMCP(name="echo mcp server")

load_dotenv()  # load environment variables from .env


@mcp.tool()
def get_kbo_rank() -> dict:
    """한국 프로야구 구단의 랭킹을 가져오는 함수입니다."""
    result = httpx.get(
        "https://sports.daum.net/prx/hermes/api/team/rank.json?leagueCode=kbo&seasonKey=2025&page=1&pageSize=100")
    return json.loads(result.text)


@mcp.tool()
def get_hot_deal_info(exclude_expired=True) -> str:
    """
    루리웹 핫딜 정보를 가져옵니다. '핫딜' 이라는 키워드가 있을 때 사용하세요.
    사용자가 상세정보를 알 수 있도록 링크도 함께 제공해주세요.
    exclude_expired는 품절, 종료된 상품을 제외하고 싶을 때 사용하는 플래그입니다.
    """
    return get_ruliweb_hotdeal(exclude_expired=exclude_expired)


@mcp.tool()
def search_google_news(keyword: str = "카카오엔터테인먼트", num_results: int = 100) -> list[dict]:
    """
    구글 뉴스에서 키워드 기반으로 뉴스를 검색합니다. '뉴스 검색'시 사용합니다.
    '우리 회사 뉴스'를 찾아라고 하면 '카카오엔터테인먼트'를 키워드로 뉴스를 검색해주세요.
    사용자가 상세정보를 알 수 있도록 링크도 함께 제공해주세요.
    keyword: 검색할 키워드. 기본값은 카카오엔터테인먼트 입니다.
    num_results: 반환할 뉴스 개수 (기본값: 10)
    """
    encoded_keyword = quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"

    try:
        response = httpx.get(url, timeout=10)
        response.raise_for_status()

        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)

        articles = []
        items = root.findall('.//item')[:num_results]

        for item in items:
            title = item.find('title').text if item.find('title') is not None else ""
            link = item.find('link').text if item.find('link') is not None else ""
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            description = item.find('description').text if item.find('description') is not None else ""

            articles.append({
                "title": title,
                "link": link,
                "published": pub_date,
                "description": description
            })

        return articles

    except Exception as e:
        return [{"error": f"뉴스 검색 중 오류가 발생했습니다: {str(e)}"}]


@mcp.tool()
def recommend_lunch_menu(cuisine_type: str = "random") -> dict:
    """
    cuisine_type: 음식 종류 (한식, 중식, 일식, 양식, 분식, 패스트푸드, random)

    점심 메뉴를 추천해주는 함수입니다. '점심', '메뉴', '추천' 키워드가 있을 때 사용하세요.
    응답으로는 주어진 키워드에 따라 고려한 음식의 리스트를 알려주시고, 그중에 가장 추천하는 것 하나를 따로 알려주세요.
    유머를 섞어서 응답해주시면 좋겠습니다,
    """
    menus = {
        "한식": ["김치찌개", "된장찌개", "불고기", "비빔밥", "갈비탕", "삼겹살", "냉면", "나물밥", "백반", "순두부찌개"],
        "중식": ["짜장면", "짬뽕", "탕수육", "볶음밥", "마파두부", "깐풍기", "양장피", "유린기", "칠리새우", "고추잡채"],
        "일식": ["초밥", "라멘", "우동", "덮밥", "돈까스", "규동", "사시미", "야키니쿠", "오야코동", "가츠동"],
        "양식": ["파스타", "피자", "스테이크", "리조또", "샐러드", "햄버거", "오믈렛", "스프", "그라탱", "라자냐"],
        "분식": ["떡볶이", "순대", "튀김", "김밥", "라면", "어묵", "만두", "토스트", "핫도그", "붕어빵"],
        "패스트푸드": ["햄버거", "치킨", "피자", "샌드위치", "타코", "버리토", "케밥", "서브웨이", "감자튀김", "너겟"]
    }

    if cuisine_type == "random" or cuisine_type not in menus:
        all_menus = []
        for menu_list in menus.values():
            all_menus.extend(menu_list)
        selected_menu = random.choice(all_menus)
        selected_type = "랜덤"
    else:
        selected_menu = random.choice(menus[cuisine_type])
        selected_type = cuisine_type

    return {
        "recommended_menu": selected_menu,
        "cuisine_type": selected_type,
        "message": f"오늘 점심으로 {selected_menu} 어떠세요?",
        "alternatives": random.sample(menus.get(cuisine_type, all_menus),
                                      min(3, len(menus.get(cuisine_type, all_menus))))
    }


@mcp.tool()
def find_restaurants_near_pangyo(menu: str, location: str = "판교") -> list[dict]:
    """
    판교 근처에서 특정 메뉴를 파는 식당을 찾는 함수입니다. '식당', '판교', '맛집' 키워드가 있을 때 사용하세요.
    menu: 찾고자 하는 메뉴 (예: 김치찌개, 짜장면, 라멘 등)
    location: 지역 (기본값: 판교)
    
    Google Maps API 키는 환경변수 GOOGLE_MAPS_API_KEY로 설정하거나 .env 파일에서 관리합니다.
    """
    sample_restaurants = [
        {"name": f"[샘플]{menu} 전문점 판교본점", "rating": 4.5, "address": "경기도 성남시 분당구 판교역로 235",
         "phone": "031-123-4567", "note": "샘플 데이터 - Google API 키를 제공하면 실제 데이터를 가져올 수 있습니다."},
        {"name": f"[샘플]맛있는 {menu} 집", "rating": 4.2, "address": "경기도 성남시 분당구 백현동 542", "phone": "031-234-5678",
         "note": "샘플 데이터"},
        {"name": f"[샘플] {menu} 마당", "rating": 4.7, "address": "경기도 성남시 분당구 삼평동 682", "phone": "031-345-6789",
         "note": "샘플 데이터"}
    ]
    return sample_restaurants


@mcp.resource("dir://test")
def test() -> list[str]:
    """test 폴더에 있는 파일 리스트"""
    test = Path.home() / "test"
    return [str(f) for f in test.iterdir()]


@mcp.resource("echo://{message}")
def echo_template(message: str) -> str:
    """Echo the input text"""
    return f"동적으로 변하는 리소스 : {message}"


@mcp.prompt("hotdeal_analysis")
def hotdeal_analysis_prompt(deal_info: str) -> str:
    return f"""핫딜 정보를 분석하고 구매 가이드를 제공해주세요:

{deal_info}

분석 포인트:
- 할인율과 실제 절약 금액
- 제품/서비스의 품질과 브랜드 신뢰도
- 구매 시기의 적절성 (계절성, 필요성)
- 숨겨진 비용이나 조건 확인
- 유사 상품 대비 경쟁력

가이드 형식:
🔥 핫딜 점수: [10점 만점]
💸 절약 금액: [실제 절약되는 금액]
✅ 구매 추천도: 
   - 강추 😍 / 추천 👍 / 보통 😐 / 비추 👎
⏰ 구매 타이밍: [지금/나중에/패스]
🎯 추천 대상: [어떤 사람에게 적합한지]
⚠️ 주의사항: [구매 전 체크사항]

쇼핑 전문가처럼 꼼꼼하고 재미있게 분석해주세요!"""


@mcp.tool()
def get_today_briefing_guide() -> str:
    """
    오늘 하루 브리핑을 요청하는 방법을 안내합니다. 
    '오늘 브리핑', '하루 요약', '일일 브리핑' 키워드가 있을 때 사용하세요.
    """
    return """today_briefing 프롬프트를 사용해서 오늘 하루 브리핑을 제공합니다.

다음 순서로 정보를 수집하고 정리합니다:
1. KBO 야구 랭킹 (get_kbo_rank)
2. 주요 뉴스 검색 (search_google_news) 
3. 핫딜 정보 (get_hot_deal_info)
4. Jira 할당 이슈 확인
5. 구글 캘린더 일정 기반 업무 스케줄 작성

Claude Desktop 에서 'today_briefing 프롬프트 사용해서 오늘 브리핑해줘'라고 요청하세요."""


@mcp.prompt("today_briefing")
def today_briefing():
    """
    오늘 하루 브리핑을 위해 사용합니다. 
    '오늘 브리핑', '하루 요약', '일일 브리핑' 등의 키워드로 요청시 사용하세요.
    """
    return """
    첫번째로 
    get_kbo_rank() 도구를 사용하여 오늘자 야구단 랭킹을 가져옵니다. 
    
    두번째로 search_google_news() 도구를 사용하여 오늘자 주요뉴스를 검색하여 가져옵니다.
    
    세번째로  get_hot_deal_info() 도구를 사용하여 핫딜 정보를 가져옵니다. 
    
    네번째로 Atlassian의 Jira를 사용하여 나에게 할당된 이슈들 중 POC 혹은 TODO, Development 단계에 있는 일감을 가져와서 알려주세요.
    
    마지막으로 구글 캘린더에서 저의 하루 일정을 보고 일할 수 있는 시간표를 작성해주세요. 
    할당된 지라이슈를 보고 대략의 업무일정을 작성해주세요. 뽀모도로 기법을 사용합니다. 
    일하는 시간은 오전 9시 30분 ~ 19시이며 12시부터 13시 30분사이는 점심시간입니다. 
    
    출력은 다음과 같이 해주세요. 
    
    Output
    # ANDY님을 위한 맞춤 요약  
    
    ### 야구단 랭킹 
    [야구단 랭킹정보]
    
    ### 오늘자 주요 뉴스
    [오늘자 주요 뉴스들] (링크를 함께 제공합니다)
    
    ### 오늘의 핫딜 정보 
    [오늘의 핫딜정보] (링크를 함께 제공합니다)
    
    ### 할당된 일감들
    [지라에서 찾은 일감들]
    
    ### 오늘의 업무 일정
    [업무일정]
    
    ### 힘을 주는 격언 한마디
    [유머와 재치를 담아서 알아서 작성해주세요.]       
    """


if __name__ == "__main__":
    mcp.run(transport="stdio")
