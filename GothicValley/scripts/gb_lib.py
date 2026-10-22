# Greybox primitives (pure Python): boxes, walls with openings, rooms, towers, roofs, stairs, spirals.
# Every solid is also a convex collision hull (UCX) unless col=False; stairs get one ramp hull per flight.
import math, json
import numpy as np

T_INT, T_EXT = 0.8, 1.6          # interior / exterior wall thickness (m), walls centred on the room outline


class Group:
    def __init__(self, name, folder):
        self.name, self.folder = name, folder
        self.prims, self.meta = [], {}

    # ---------------------------------------------------------------- raw solids
    def add(self, v, f, mat, col=True):
        self.prims.append(dict(v=np.round(np.asarray(v, float), 3).tolist(), f=f, m=mat, col=col))

    def box(self, x0, x1, y0, y1, z0, z1, mat, col=True):
        if x1 - x0 < 0.02 or y1 - y0 < 0.02 or z1 - z0 < 0.02:
            return
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        self.add(v, f, mat, col)

    def poly_prism(self, pts, z0, z1, mat, col=True):
        """Vertical prism over a convex polygon (counter-clockwise points)."""
        n = len(pts)
        v = [(x, y, z0) for x, y in pts] + [(x, y, z1) for x, y in pts]
        f = [list(range(n))[::-1], list(range(n, 2 * n))] + [[i, (i + 1) % n, n + (i + 1) % n, n + i] for i in range(n)]
        self.add(v, f, mat, col)

    def cyl(self, cx, cy, r, z0, z1, mat, sides=16, col=True):
        self.poly_prism([(cx + r * math.cos(2 * math.pi * k / sides), cy + r * math.sin(2 * math.pi * k / sides)) for k in range(sides)],
                        z0, z1, mat, col)

    def cone(self, cx, cy, r, z0, z1, mat, sides=16, col=True):
        v = [(cx + r * math.cos(2 * math.pi * k / sides), cy + r * math.sin(2 * math.pi * k / sides), z0) for k in range(sides)] + [(cx, cy, z1)]
        f = [list(range(sides))[::-1]] + [[k, (k + 1) % sides, sides] for k in range(sides)]
        self.add(v, f, mat, col)

    def pyramid(self, x0, x1, y0, y1, z0, z1, mat, col=True):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (cx, cy, z1)]
        self.add(v, [[0, 3, 2, 1], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]], mat, col)

    def gable(self, x0, x1, y0, y1, z0, z1, mat, axis="x", col=True, overhang=0.4):
        """Pitched roof, ridge parallel to `axis`."""
        x0, x1, y0, y1 = x0 - overhang, x1 + overhang, y0 - overhang, y1 + overhang
        if axis == "x":
            ym = (y0 + y1) / 2
            v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, ym, z1), (x1, ym, z1)]
            f = [[0, 3, 2, 1], [0, 1, 5, 4], [2, 3, 4, 5], [0, 4, 3], [1, 2, 5]]
        else:
            xm = (x0 + x1) / 2
            v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (xm, y0, z1), (xm, y1, z1)]
            f = [[0, 3, 2, 1], [0, 4, 5, 3], [1, 2, 5, 4], [0, 1, 4], [2, 3, 5]]
        self.add(v, f, mat, col)

    def roof_trunc(self, x0, x1, y0, y1, z0, z_top, pitch_deg, mat, axis="x", col=True, overhang=0.4):
        """Roof at `pitch_deg`, ridge parallel to `axis`; if the ridge would pass z_top the top is flat (held at z_top)."""
        x0, x1, y0, y1 = x0 - overhang, x1 + overhang, y0 - overhang, y1 + overhang
        t = math.tan(math.radians(pitch_deg))
        w = ((y1 - y0) if axis == "x" else (x1 - x0)) / 2
        zt = min(z_top, z0 + w * t)
        inset = (zt - z0) / t
        if axis == "x":
            a, b = y0 + inset, y1 - inset
            v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, a, zt), (x1, a, zt), (x1, b, zt), (x0, b, zt)]
        else:
            a, b = x0 + inset, x1 - inset
            v = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (a, y0, zt), (b, y0, zt), (b, y1, zt), (a, y1, zt)]
        self.add(v, [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], mat, col)

    def ramp(self, p0, p1, width, z0, z1, thick=0.4, mat="GB_Stone", col=True, visible=True):
        """Inclined slab from p0 (at z0) to p1 (at z1), `width` wide (walkable collision for stairs and ramps)."""
        p0, p1 = np.array(p0, float), np.array(p1, float)
        d = p1 - p0; L = np.linalg.norm(d); d /= L
        n = np.array([-d[1], d[0]]) * width / 2
        a, b, c, e = p0 - n, p0 + n, p1 + n, p1 - n
        v = [(*a, z0 - thick), (*b, z0 - thick), (*c, z1 - thick), (*e, z1 - thick), (*a, z0), (*b, z0), (*c, z1), (*e, z1)]
        f = [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        if visible:
            self.add(v, f, mat, col)
        elif col:
            self.add(v, f, mat, "only")

    # ---------------------------------------------------------------- walls, rooms
    def wall(self, axis, a0, a1, u0, u1, z0, z1, mat, holes=(), col=True):
        """Wall slab: axis 'x' = wall runs along X (u) and is thick in Y (a0..a1); 'y' = runs along Y, thick in X."""
        for (r0, r1, v0, v1) in rect_minus((u0, u1, z0, z1), holes):
            if axis == "x":
                self.box(r0, r1, a0, a1, v0, v1, mat, col)
            else:
                self.box(a0, a1, r0, r1, v0, v1, mat, col)

    def room(self, R, doors=(), windows=(), mat_wall="GB_Interior", mat_floor="GB_Floor", mat_ceil="GB_Interior",
             floor=True, ceil=True, t=T_INT, floor_t=0.3, holes_floor=(), holes_ceil=(), walls=("n", "s", "e", "w")):
        """R = dict(x0,x1,y0,y1,z0,z1): interior clear volume. doors/windows: (side, u0, u1, v0, v1) with side n,s,e,w and
        u along the wall (world Y for the n/s walls, world X for the e/w walls), v in world Z."""
        x0, x1, y0, y1, z0, z1 = R["x0"], R["x1"], R["y0"], R["y1"], R["z0"], R["z1"]
        h = t / 2
        ops = {s: [] for s in "nsew"}
        for s, u0, u1, v0, v1 in list(doors) + list(windows):
            ops[s].append((u0, u1, v0, v1))
        if "n" in walls:
            self.wall("y", x1 - h, x1 + h, y0 - h, y1 + h, z0 - floor_t, z1 + floor_t, mat_wall, ops["n"])
        if "s" in walls:
            self.wall("y", x0 - h, x0 + h, y0 - h, y1 + h, z0 - floor_t, z1 + floor_t, mat_wall, ops["s"])
        if "e" in walls:
            self.wall("x", y1 - h, y1 + h, x0 + h, x1 - h, z0 - floor_t, z1 + floor_t, mat_wall, ops["e"])
        if "w" in walls:
            self.wall("x", y0 - h, y0 + h, x0 + h, x1 - h, z0 - floor_t, z1 + floor_t, mat_wall, ops["w"])
        if floor:
            for (a0, a1, b0, b1) in rect_minus((x0 - h, x1 + h, y0 - h, y1 + h), holes_floor):
                self.box(a0, a1, b0, b1, z0 - floor_t, z0, mat_floor)
        if ceil:
            for (a0, a1, b0, b1) in rect_minus((x0 - h, x1 + h, y0 - h, y1 + h), holes_ceil):
                self.box(a0, a1, b0, b1, z1, z1 + floor_t, mat_ceil)

    # ---------------------------------------------------------------- vertical circulation
    def stairs(self, p0, direction, width, z0, z1, mat="GB_Stone", step_h=0.2, run=0.3, landing_every=None, solid=True):
        """Straight flight from p0 (xy at the first step) towards `direction` (unit xy), rising z0 -> z1.
        Visual steps (no collision) + one walkable ramp hull per flight. Returns the top xy."""
        d = np.array(direction, float); d /= np.linalg.norm(d)
        nvec = np.array([-d[1], d[0]])
        n = max(1, int(round((z1 - z0) / step_h)))
        sh = (z1 - z0) / n
        p = np.array(p0, float)
        start = p.copy(); zc = z0
        for i in range(n):
            a = p + d * run * i; b = a + d * run
            q = [a - nvec * width / 2, b - nvec * width / 2, b + nvec * width / 2, a + nvec * width / 2]
            zb = z0 - 0.4 if not solid else z0 - 0.2
            self.add([(*q[k], zb if solid else z0 + sh * i - 0.25) for k in range(4)] + [(*q[k], z0 + sh * (i + 1)) for k in range(4)],
                     [[0, 3, 2, 1], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], mat, False)
        top = p + d * run * n
        self.ramp(start - d * 0.05, top, width, z0, z1, 0.4, mat, col=True, visible=False)
        return top

    def spiral(self, cx, cy, r_out, z0, z1, mat="GB_Stone", step_h=0.2, deg_per_step=15, start_deg=0, core=0.45, shaft=True,
               shaft_mat="GB_Interior", openings=(), t=0.6, shaft_r=None):
        """Spiral stair (r_out = outer radius). Steps are wedges, each a convex collision hull. Openings: list of
        (angle_deg, z_bottom, width_m, height_m) cut into the cylindrical shaft wall."""
        n = max(1, int(round((z1 - z0) / step_h)))
        sh = (z1 - z0) / n
        for i in range(n):
            a0 = math.radians(start_deg + deg_per_step * i); a1 = a0 + math.radians(deg_per_step + 2)
            zt = z0 + sh * (i + 1)
            pts = [(cx + core * math.cos(a0), cy + core * math.sin(a0)), (cx + r_out * math.cos(a0), cy + r_out * math.sin(a0)),
                   (cx + r_out * math.cos(a1), cy + r_out * math.sin(a1)), (cx + core * math.cos(a1), cy + core * math.sin(a1))]
            self.poly_prism(pts, zt - 0.35, zt, mat, True)
        self.cyl(cx, cy, core, z0, z1, mat, 8, True)
        if shaft:                                      # cylindrical shaft wall made of panels, with door openings
            sides = 20
            for k in range(sides):
                a0 = 2 * math.pi * k / sides; a1 = 2 * math.pi * (k + 1) / sides
                am = math.degrees((a0 + a1) / 2) % 360
                ri = (shaft_r or r_out) + 0.05; ro = ri + t
                zs = [(z0 - 0.3, z1 + 0.3)]
                for (ang, zb, w, hgt) in openings:
                    dang = (am - ang + 180) % 360 - 180
                    if abs(math.radians(dang)) * ri < w / 2 + 0.3:
                        zs = [s for seg in zs for s in ((seg[0], min(seg[1], zb)), (max(seg[0], zb + hgt), seg[1])) if s[1] - s[0] > 0.05]
                for za, zb_ in zs:
                    pts = [(cx + ri * math.cos(a0), cy + ri * math.sin(a0)), (cx + ro * math.cos(a0), cy + ro * math.sin(a0)),
                           (cx + ro * math.cos(a1), cy + ro * math.sin(a1)), (cx + ri * math.cos(a1), cy + ri * math.sin(a1))]
                    self.poly_prism(pts, za, zb_, shaft_mat, True)

    def ring_wall(self, cx, cy, r_in, r_out, z0, z1, mat="GB_Stone", openings=(), sides=20):
        """Round tower wall made of convex panels; openings = (angle_deg, z_bottom, width_m, height_m)."""
        for k in range(sides):
            a0 = 2 * math.pi * k / sides; a1 = 2 * math.pi * (k + 1) / sides
            am = math.degrees((a0 + a1) / 2) % 360
            zs = [(z0, z1)]
            for (ang, zb, w, hgt) in openings:
                dang = (am - ang + 180) % 360 - 180
                if abs(math.radians(dang)) * r_in < w / 2 + 0.3:
                    zs = [s for seg in zs for s in ((seg[0], min(seg[1], zb)), (max(seg[0], zb + hgt), seg[1])) if s[1] - s[0] > 0.05]
            for za, zb_ in zs:
                pts = [(cx + r_in * math.cos(a0), cy + r_in * math.sin(a0)), (cx + r_out * math.cos(a0), cy + r_out * math.sin(a0)),
                       (cx + r_out * math.cos(a1), cy + r_out * math.sin(a1)), (cx + r_in * math.cos(a1), cy + r_in * math.sin(a1))]
                self.poly_prism(pts, za, zb_, mat, True)

    def floor_ring(self, x0, x1, y0, y1, z, hole, mat="GB_Stone", thick=0.3):
        """Landing slab filling a stair tower at level z, with a square hole around the spiral."""
        for (a0, a1, b0, b1) in rect_minus((x0, x1, y0, y1), [hole]):
            self.box(a0, a1, b0, b1, z - thick, z, mat)

    def annulus(self, cx, cy, r0, r1, z, mat="GB_Stone", thick=0.3, sides=20):
        for k in range(sides):
            a0 = 2 * math.pi * k / sides; a1 = 2 * math.pi * (k + 1) / sides
            pts = [(cx + r0 * math.cos(a0), cy + r0 * math.sin(a0)), (cx + r1 * math.cos(a0), cy + r1 * math.sin(a0)),
                   (cx + r1 * math.cos(a1), cy + r1 * math.sin(a1)), (cx + r0 * math.cos(a1), cy + r0 * math.sin(a1))]
            self.poly_prism(pts, z - thick, z, mat, True)

    def to_json(self):
        return dict(name=self.name, folder=self.folder, prims=self.prims, meta=self.meta)


def rect_minus(r, holes):
    """Axis-aligned rectangle r=(u0,u1,v0,v1) minus holes -> list of rectangles."""
    out = [r]
    for h in holes:
        nxt = []
        for (u0, u1, v0, v1) in out:
            hu0, hu1, hv0, hv1 = max(u0, h[0]), min(u1, h[1]), max(v0, h[2]), min(v1, h[3])
            if hu0 >= hu1 or hv0 >= hv1:
                nxt.append((u0, u1, v0, v1)); continue
            if u0 < hu0: nxt.append((u0, hu0, v0, v1))
            if hu1 < u1: nxt.append((hu1, u1, v0, v1))
            if v0 < hv0: nxt.append((hu0, hu1, v0, hv0))
            if hv1 < v1: nxt.append((hu0, hu1, hv1, v1))
        out = nxt
    return [o for o in out if o[1] - o[0] > 0.02 and o[3] - o[2] > 0.02]


def rect_room(name, x0, x1, y0, y1, z0, h):
    return dict(name=name, x0=x0, x1=x1, y0=y0, y1=y1, z0=z0, z1=z0 + h)


def save(groups, path):
    json.dump([g.to_json() for g in groups], open(path, "w"))
