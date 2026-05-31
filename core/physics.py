"""pymunk 7 기반 물리 월드 — Time Backer

설계 원칙:
  - 지면 충돌(중력·착지)만 pymunk가 담당한다.
  - 플레이어·적은 ShapeFilter로 서로 통과하도록 설정.
  - 스파이크·출구·스위치·적 충돌 판정은 GameScene에서 rect 체크로 처리.
"""

import math
import pymunk

# ── Collision types ──────────────────────────────────────────────────────
CT_PLAYER = 1
CT_GROUND = 2
CT_ENEMY  = 3

# ── ShapeFilter categories ───────────────────────────────────────────────
_CAT_PLAYER = 0b001
_CAT_ENEMY  = 0b010
_CAT_GROUND = 0b100

# 플레이어·적은 지면과만 충돌, 서로 통과
FILTER_PLAYER = pymunk.ShapeFilter(categories=_CAT_PLAYER, mask=_CAT_GROUND)
FILTER_ENEMY  = pymunk.ShapeFilter(categories=_CAT_ENEMY,  mask=_CAT_GROUND)
FILTER_GROUND = pymunk.ShapeFilter(
    categories=_CAT_GROUND, mask=_CAT_PLAYER | _CAT_ENEMY
)

# ── Physics constants ────────────────────────────────────────────────────
GRAVITY_PPS2: float = 2160.0   # px/s²  (원본: 0.6 px/frame² × 60²)
JUMP_VY:      float = -780.0   # px/s   (원본: -13 px/frame)
MOVE_VX:      float = 180.0    # px/s   (원본:   3 px/frame)
STOMP_VY:     float = -480.0   # px/s   (원본:  -8 px/frame)
_DT:          float = 1.0 / 60


class PhysicsWorld:
    """pymunk Space 래퍼.

    매 ``step()`` 호출 후 ``player_on_ground`` 플래그가 갱신된다.
    충돌 감지(스파이크·출구·적)는 GameScene이 rect 체크로 처리한다.
    """

    def __init__(self) -> None:
        self.space = pymunk.Space()
        self.space.gravity     = (0.0, GRAVITY_PPS2)
        self.space.damping     = 1.0    # 공기저항 없음
        self.space.collision_slop = 0.5 # 허용 침투 거리(px)

        self.player_on_ground = False
        self._on_ground_buf   = [False]   # 클로저에서 수정 가능한 mutable 컨테이너

        self._setup_handlers()

    # ── 핸들러 ────────────────────────────────────────────────────────────

    def _setup_handlers(self) -> None:
        buf = self._on_ground_buf

        def player_ground_pre(arb: pymunk.Arbiter, space, data) -> None:
            n = arb.contact_point_set.normal
            # n.y > 0 → 법선이 아래쪽 = 플레이어가 지면 위에 있음
            if n.y > 0.3:
                buf[0] = True

        self.space.on_collision(CT_PLAYER, CT_GROUND, pre_solve=player_ground_pre)

    # ── 스텝 ──────────────────────────────────────────────────────────────

    def step(self) -> None:
        self._on_ground_buf[0] = False
        self.space.step(_DT)
        self.player_on_ground = self._on_ground_buf[0]

    # ── 바디 생성 ─────────────────────────────────────────────────────────

    def add_player_body(self, x: float, y: float, w: float, h: float) -> pymunk.Body:
        body  = pymunk.Body(1.0, math.inf)
        body.position = (x + w / 2, y + h / 2)
        shape = pymunk.Poly.create_box(body, (w - 1, h - 1))  # 1 px 여유
        shape.collision_type = CT_PLAYER
        shape.friction       = 0.0
        shape.elasticity     = 0.0
        shape.filter         = FILTER_PLAYER
        self.space.add(body, shape)
        return body

    def add_enemy_body(self, x: float, y: float, w: float, h: float) -> pymunk.Body:
        body  = pymunk.Body(1.0, math.inf)
        body.position = (x + w / 2, y + h / 2)
        shape = pymunk.Poly.create_box(body, (w - 1, h - 1))
        shape.collision_type = CT_ENEMY
        shape.friction       = 0.0
        shape.elasticity     = 0.0
        shape.filter         = FILTER_ENEMY
        self.space.add(body, shape)
        return body

    def add_static_ground(self, x: float, y: float, w: float, h: float) -> None:
        body  = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (x + w / 2, y + h / 2)
        shape = pymunk.Poly.create_box(body, (w, h))
        shape.collision_type = CT_GROUND
        shape.friction       = 0.8
        shape.elasticity     = 0.0
        shape.filter         = FILTER_GROUND
        self.space.add(body, shape)

    def remove_body(self, body: pymunk.Body) -> None:
        for shape in list(body.shapes):
            if shape in self.space.shapes:
                self.space.remove(shape)
        if body in self.space.bodies:
            self.space.remove(body)
