import math
import pymunk

CT_PLAYER = 1
CT_GROUND = 2
CT_ENEMY = 3

CAT_PLAYER = 1
CAT_ENEMY = 2
CAT_GROUND = 4

FILTER_PLAYER = pymunk.ShapeFilter(categories=CAT_PLAYER, mask=CAT_GROUND)
FILTER_ENEMY = pymunk.ShapeFilter(categories=CAT_ENEMY, mask=CAT_GROUND)
FILTER_GROUND = pymunk.ShapeFilter(categories=CAT_GROUND, mask=CAT_PLAYER | CAT_ENEMY)
FILTER_DISABLED = pymunk.ShapeFilter(mask=0)  # 충돌 없음

GRAVITY_PPS2 = 2160.0
JUMP_VY = -780.0
MOVE_VX = 180.0
STOMP_VY = -480.0
DT = 1.0 / 60


class PhysicsWorld:
    def __init__(self):
        self.space = pymunk.Space()
        self.space.gravity = (0.0, GRAVITY_PPS2)
        self.space.damping = 1.0
        self.space.collision_slop = 0.5

        self.player_on_ground = False
        self.on_ground_buffer = [False]
        self.space.on_collision(CT_PLAYER, CT_GROUND, pre_solve=self.player_ground_pre)

    def player_ground_pre(self, arb, space, data):
        if arb.contact_point_set.normal.y > 0.3:
            self.on_ground_buffer[0] = True

    def step(self):
        self.on_ground_buffer[0] = False
        self.space.step(DT)
        self.player_on_ground = self.on_ground_buffer[0]

    def add_dynamic_body(self, x, y, w, h, ct, filt):
        body = pymunk.Body(1.0, math.inf)
        body.position = (x + w / 2, y + h / 2)
        shape = pymunk.Poly.create_box(body, (w - 1, h - 1))
        shape.collision_type = ct
        shape.friction = 0.0
        shape.elasticity = 0.0
        shape.filter = filt
        self.space.add(body, shape)
        return body

    def add_player_body(self, x, y, w, h):
        return self.add_dynamic_body(x, y, w, h, CT_PLAYER, FILTER_PLAYER)

    def add_enemy_body(self, x, y, w, h):
        return self.add_dynamic_body(x, y, w, h, CT_ENEMY, FILTER_ENEMY)

    def add_static_ground(self, x, y, w, h):
        self.make_static(x, y, w, h, FILTER_GROUND)

    def add_gate(self, x, y, w, h):
        return self.make_static(x, y, w, h, FILTER_DISABLED)

    def enable_gate(self, shape):
        shape.filter = FILTER_GROUND

    def make_static(self, x, y, w, h, filt):
        body = pymunk.Body(body_type=pymunk.Body.STATIC)
        body.position = (x + w / 2, y + h / 2)
        shape = pymunk.Poly.create_box(body, (w, h))
        shape.collision_type = CT_GROUND
        shape.friction = 0.8
        shape.elasticity = 0.0
        shape.filter = filt
        self.space.add(body, shape)
        return shape

    def remove_body(self, body):
        for shape in list(body.shapes):
            if shape in self.space.shapes:
                self.space.remove(shape)
        if body in self.space.bodies:
            self.space.remove(body)
