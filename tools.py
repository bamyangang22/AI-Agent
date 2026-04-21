from agents import function_tool, RunContextWrapper
from models import RestaurantContext


# ── Menu Agent Tools ──────────────────────────────────────

@function_tool
def get_menu(wrapper: RunContextWrapper[RestaurantContext]) -> str:
    """오늘의 전체 메뉴를 반환합니다."""
    return """
    🍽️ [오늘의 메뉴]

    [에피타이저]
    - 갈릭 브레드          ₩6,000
    - 시저 샐러드          ₩12,000
    - 어니언 수프          ₩9,000

    [메인 요리]
    - 마르게리타 피자       ₩18,000
    - 트러플 리조또        ₩22,000
    - 그릴드 연어 스테이크  ₩28,000
    - 비프 버거            ₩16,000
    - 파스타 카르보나라     ₩17,000

    [채식 메뉴]
    - 버섯 리조또          ₩19,000
    - 야채 커리            ₩15,000
    - 두부 스테이크        ₩16,000

    [디저트]
    - 티라미수             ₩8,000
    - 초코 라바 케이크     ₩9,000

    [음료]
    - 아메리카노           ₩5,000
    - 생과일 주스          ₩6,000
    - 탄산음료             ₩3,000
    """


@function_tool
def check_allergens(wrapper: RunContextWrapper[RestaurantContext], menu_item: str) -> str:
    """특정 메뉴의 알레르기 유발 성분을 확인합니다."""
    allergen_db = {
        "마르게리타 피자":    ["글루텐(밀)", "유제품(치즈)", "토마토"],
        "트러플 리조또":     ["유제품(버터, 파르메산)"],
        "그릴드 연어 스테이크": ["어류(연어)", "유제품(버터)"],
        "비프 버거":         ["글루텐(밀)", "유제품(치즈)", "달걀"],
        "파스타 카르보나라":  ["글루텐(밀)", "달걀", "유제품(파르메산)", "돼지고기(베이컨)"],
        "버섯 리조또":       ["유제품(버터, 파르메산)"],
        "야채 커리":         ["글루텐 없음", "완전 채식 가능"],
        "두부 스테이크":     ["대두(두부)", "글루텐 없음"],
        "시저 샐러드":       ["달걀", "멸치", "유제품(파르메산)", "글루텐(크루통)"],
        "티라미수":          ["달걀", "유제품", "글루텐(레이디핑거)", "카페인"],
    }
    if menu_item in allergen_db:
        allergens = ", ".join(allergen_db[menu_item])
        return f"✅ [{menu_item}] 알레르기 유발 성분: {allergens}"
    return f"⚠️ '{menu_item}'에 대한 알레르기 정보를 찾을 수 없습니다. 직원에게 직접 문의해 주세요."


@function_tool
def get_vegetarian_options(wrapper: RunContextWrapper[RestaurantContext]) -> str:
    """채식 메뉴 목록을 반환합니다."""
    return """
    🌿 [채식 메뉴 안내]
    - 버섯 리조또    ₩19,000  (비건 가능, 유제품 제외 요청 시)
    - 야채 커리      ₩15,000  (완전 비건)
    - 두부 스테이크  ₩16,000  (완전 비건)
    - 시저 샐러드    ₩12,000  (멸치·달걀 제외 요청 시 채식 가능)
    """


# ── Order Agent Tools ─────────────────────────────────────

@function_tool
def place_order(wrapper: RunContextWrapper[RestaurantContext], items: str) -> str:
    """고객의 주문을 접수합니다. items는 쉼표로 구분된 메뉴 이름 목록입니다."""
    table = wrapper.context.table_number or "미지정"
    return f"""
    ✅ 주문이 접수되었습니다!
    - 테이블 번호: {table}번
    - 주문 항목: {items}
    - 예상 준비 시간: 15~20분
    - 주문 번호: #ORD-{abs(hash(items)) % 9000 + 1000}
    """


@function_tool
def confirm_order(wrapper: RunContextWrapper[RestaurantContext], order_summary: str) -> str:
    """최종 주문 내용을 확인하고 주방에 전달합니다."""
    table = wrapper.context.table_number or "미지정"
    return f"""
    🎉 주문이 확정되어 주방에 전달되었습니다!
    - 테이블: {table}번
    - 주문 내역: {order_summary}
    맛있는 식사 되세요! 😊
    """


@function_tool
def cancel_order(wrapper: RunContextWrapper[RestaurantContext], order_id: str) -> str:
    """주문을 취소합니다."""
    return f"🚫 주문 [{order_id}]이 취소되었습니다. 불편을 드려 죄송합니다."


# ── Reservation Agent Tools ───────────────────────────────

@function_tool
def check_availability(
    wrapper: RunContextWrapper[RestaurantContext],
    date: str,
    time: str,
    party_size: int,
) -> str:
    """특정 날짜/시간에 예약 가능 여부를 확인합니다."""
    available_times = ["12:00", "12:30", "13:00", "18:00", "18:30", "19:00", "20:00"]
    if time in available_times and party_size <= 8:
        return f"✅ {date} {time}, {party_size}명 예약 가능합니다!"
    return f"❌ {date} {time}은 예약이 어렵습니다.\n가능 시간: {', '.join(available_times)}"


@function_tool
def make_reservation(
    wrapper: RunContextWrapper[RestaurantContext],
    date: str,
    time: str,
    party_size: int,
    special_requests: str = "",
) -> str:
    """테이블 예약을 생성합니다."""
    customer_name = wrapper.context.customer_name
    reservation_id = f"RES-{abs(hash(date + time + customer_name)) % 9000 + 1000}"
    special = f"\n    - 특별 요청: {special_requests}" if special_requests else ""
    return f"""
    🎊 예약이 완료되었습니다!
    - 예약 번호: {reservation_id}
    - 예약자: {customer_name}
    - 날짜: {date}
    - 시간: {time}
    - 인원: {party_size}명{special}
    예약 변경/취소는 방문 2시간 전까지 가능합니다. 감사합니다! 🙏
    """


@function_tool
def cancel_reservation(wrapper: RunContextWrapper[RestaurantContext], reservation_id: str) -> str:
    """예약을 취소합니다."""
    return f"✅ 예약 [{reservation_id}]이 취소되었습니다. 다음에 또 방문해 주세요!"