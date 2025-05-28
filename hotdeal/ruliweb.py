import re

import httpx
from bs4 import BeautifulSoup


def is_expired_post(title):
    """
    게시글 제목이 품절/종료된 핫딜인지 확인하는 함수

    Args:
        title (str): 게시글 제목

    Returns:
        bool: 품절/종료된 게시글이면 True, 아니면 False
    """
    if not title:
        return False

    # 품절/종료 키워드 목록
    expired_keywords = ['품절', '종료', '마감', '완료']

    # 대소문자 구분 없이 확인
    title_lower = title.lower()

    for keyword in expired_keywords:
        if keyword in title_lower:
            return True

    return False


def parse_ruliweb_hotdeal(html_content, exclude_expired=True):
    """
    루리웹 핫딜 게시판 HTML에서 게시글 정보를 추출하는 함수

    Args:
        html_content (str): HTML 문자열
        exclude_expired (bool): 품절/종료된 게시글 제외 여부 (기본값: True)

    Returns:
        list: 게시글 정보가 담긴 딕셔너리 리스트
    """
    soup = BeautifulSoup(html_content, 'html.parser')

    # "table_body default_list blocktarget" 클래스를 가진 모든 tr 태그 찾기
    post_items = soup.find_all('tr', class_='table_body default_list blocktarget')

    posts = []

    for item in post_items:
        try:
            post_data = {}

            # 카테고리 추출
            category_elem = item.find('a', class_='cate_label')
            if category_elem:
                category_text = category_elem.get_text(strip=True)
                # [대괄호] 제거
                post_data['category'] = category_text.strip('[]')
            else:
                post_data['category'] = ''

            # 제목과 링크 추출
            title_elem = item.find('a', class_='subject_link deco')
            if title_elem:
                post_data['title'] = title_elem.get_text(strip=True)
                post_data['link'] = title_elem.get('href', '')
            else:
                post_data['title'] = ''
                post_data['link'] = ''

            # 품절/종료 게시글 제외 옵션이 활성화된 경우 필터링
            if exclude_expired and is_expired_post(post_data['title']):
                continue

            # 이미지 여부 확인
            image_icon = title_elem.find('i', class_='icon-picture') if title_elem else None
            post_data['has_image'] = image_icon is not None

            # 추천수 추출
            recommend_elem = item.find('span', class_=re.compile(r'recomd'))
            if recommend_elem:
                recommend_text = recommend_elem.get_text(strip=True)
                recommend_num = re.findall(r'\d+', recommend_text)
                post_data['recommend'] = int(recommend_num[0]) if recommend_num else 0
            else:
                post_data['recommend'] = 0

            # 댓글수 추출
            reply_elem = item.find('span', class_=re.compile(r'replycount'))
            if reply_elem:
                reply_num_elem = reply_elem.find('span', class_='num')
                if reply_num_elem:
                    post_data['replies'] = int(reply_num_elem.get_text(strip=True))
                else:
                    post_data['replies'] = 0
            else:
                post_data['replies'] = 0

            # 조회수 추출
            hit_elem = item.find('span', class_=re.compile(r'hit'))
            if hit_elem:
                hit_text = hit_elem.get_text(strip=True)
                hit_num = re.findall(r'[\d,]+', hit_text)
                if hit_num:
                    # 쉼표 제거 후 정수 변환
                    post_data['views'] = int(hit_num[0].replace(',', ''))
                else:
                    post_data['views'] = 0
            else:
                post_data['views'] = 0

            # 작성시간 추출
            time_elem = item.find('span', class_='time')
            if time_elem:
                post_data['time'] = time_elem.get_text(strip=True)
            else:
                post_data['time'] = ''

            # 작성자 추출
            writer_elem = item.find('span', class_='writer text_over')
            if writer_elem:
                post_data['writer'] = writer_elem.get_text(strip=True)
            else:
                post_data['writer'] = ''

            # 작성자 ID 추출 (숨겨진 input에서)
            member_srl_elem = item.find('input', class_='member_srl')
            if member_srl_elem:
                post_data['member_id'] = member_srl_elem.get('value', '')
            else:
                post_data['member_id'] = ''

            posts.append(post_data)

        except Exception as e:
            print(f"항목 파싱 중 오류 발생: {e}")
            continue

    return posts


def get_ruliweb_hotdeal(exclude_expired=True):
    """루리웹 핫딜 정보를 가져오는 함수"""
    result = httpx.get("https://m.ruliweb.com/market/board/1020")
    return parse_ruliweb_hotdeal(result.text, exclude_expired=exclude_expired)
