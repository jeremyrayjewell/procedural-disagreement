"""Tests of the renderer-independent core. Run with:  python -m unittest discover tests"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from procedural_disagreement.core import choreography as ch  # noqa: E402
from procedural_disagreement.core import layout, outer, profiles, stablehash, timeline, variants  # noqa: E402
from procedural_disagreement.core.vec import dot, length, normalize, q_rotate, sub  # noqa: E402


def section_times(step=0.1):
    t = timeline.SECTION_START
    while t <= timeline.SECTION_END:
        yield t
        t += step


def q_axis_angle_z(degrees):
    from procedural_disagreement.core.vec import q_axis_angle
    return q_axis_angle((0.0, 0.0, 1.0), degrees)


class TimelineTests(unittest.TestCase):
    def test_frames_are_absolute_track_time(self):
        self.assertEqual(timeline.frame_of(35.0), 1050)
        self.assertEqual(timeline.frame_of(timeline.SECTION_END) - timeline.frame_of(timeline.SECTION_START), 900)
        self.assertAlmostEqual(timeline.time_of(1050), 35.0)

    def test_parse_time(self):
        self.assertEqual(timeline.parse_time("35"), 35.0)
        self.assertEqual(timeline.parse_time("1:05"), 65.0)
        self.assertEqual(timeline.parse_time("0:48.5"), 48.5)
        self.assertEqual(timeline.parse_time("0:01:05"), 65.0)


class CueTests(unittest.TestCase):
    def test_cues_are_inside_the_section_and_in_narrative_order(self):
        order = ("plane_a_enter", "plane_a_arrive", "disagreement_start", "divergence_end", "primary_cut",
                 "primary_infrastructure_failure", "alternate_cut", "alternate_infrastructure_failure")
        times = [timeline.cue(name) for name in order]
        self.assertEqual(times, sorted(times))
        self.assertLessEqual(timeline.PLANE_B_ENTER, timeline.PLANE_B_ARRIVE)
        self.assertLessEqual(timeline.PLANE_B_ARRIVE, timeline.DISAGREEMENT_START)
        for name in ("plane_a_enter", "plane_b_retreat_end", "camera_emphasis", "alternate_region_at_rest"):
            self.assertGreaterEqual(timeline.cue(name), timeline.SECTION_START)
            self.assertLessEqual(timeline.cue(name), timeline.SECTION_END)

    def test_missing_cue_is_reported_by_name(self):
        with self.assertRaisesRegex(KeyError, "no_such_cue"):
            timeline.cue("no_such_cue")

    def test_cyclic_motion_is_locked_to_the_beat(self):
        v = variants.primary()
        # Six blades, one passing per beat.
        self.assertAlmostEqual(ch.rotor_angle(v, timeline.DOWNBEAT + timeline.BEAT, ch.NEVER)
                               - ch.rotor_angle(v, timeline.DOWNBEAT, ch.NEVER), 60.0)
        # A conduit pulse leaves the body on the downbeat and every two beats after.
        on = ch.conduit_energy(0.0, timeline.DOWNBEAT + 2 * timeline.BEAT, ch.NEVER, 1.0)
        off = ch.conduit_energy(0.0, timeline.DOWNBEAT + timeline.BEAT, ch.NEVER, 1.0)
        self.assertAlmostEqual(on, 1.0)
        self.assertLess(off, 0.3)

    def test_plane_is_visible_within_frames_of_its_cue(self):
        p, a = variants.primary(), variants.alternate()
        self.assertEqual(ch.plane_pose(ch.PLANE_A, p, a, timeline.PLANE_A_ENTER)[3], 0.0)
        self.assertGreater(ch.plane_pose(ch.PLANE_A, p, a, timeline.PLANE_A_ENTER + 0.1)[3], 0.6)

    def test_camera_surges_on_its_emphasis_cue(self):
        def speed(t):
            return length(sub(ch.camera_pose(t + 1.0 / timeline.FPS)[0], ch.camera_pose(t)[0]))
        self.assertGreater(speed(timeline.CAMERA_EMPHASIS), 2.5 * speed(timeline.CAMERA_EMPHASIS - 0.5))


class DirectorialPassTests(unittest.TestCase):
    """0:55 the alternate procedure acts; 1:00 the disagreement spreads into the system."""

    def test_alternate_cut_opens_a_gap_quickly(self):
        a = variants.alternate()
        self.assertAlmostEqual(length(ch.detach_pose(a, a.cut_time)[0]), 0.0)
        # Most of the gap within a third of a second, before the slow travel has begun.
        self.assertGreater(length(ch.detach_pose(a, a.cut_time + 0.33)[0]), 0.18)
        # The primary's release is unchanged.
        p = variants.primary()
        self.assertLess(length(ch.detach_pose(p, p.cut_time + 0.33)[0]), 0.05)

    def test_stump_recoils_on_the_cut_and_holds(self):
        a = variants.alternate()

        def degrees(t):
            return math.degrees(2.0 * math.acos(min(1.0, abs(ch.stump_pose(a, t)[0]))))

        self.assertAlmostEqual(degrees(a.cut_time), 0.0)
        self.assertAlmostEqual(degrees(a.cut_time + a.release_duration), a.stump_recoil, places=4)
        self.assertAlmostEqual(degrees(timeline.SECTION_END), a.stump_recoil, places=4)
        self.assertAlmostEqual(degrees(a.cut_time - 5.0), 0.0)

    def test_alternate_steps_away_from_the_primary_as_it_acts(self):
        a = variants.alternate()
        before = length(ch.reality_offset(a, a.cut_time))
        after = length(ch.reality_offset(a, a.cut_time + a.release_duration))
        self.assertAlmostEqual(after / before, 1.0 + a.act_divergence)

    def test_system_branch_starts_exactly_on_its_cue(self):
        cue = timeline.SYSTEM_DIVERGENCE
        self.assertEqual(ch.system_branch_presence(cue), 0.0)
        self.assertEqual(ch.system_branch_angle(cue), 0.0)
        self.assertEqual(ch.system_branch_presence(cue - 10.0), 0.0)
        self.assertEqual(ch.system_branch_presence(cue + 0.2), 1.0)
        # Visibly apart within a beat, and still drifting at the end.
        self.assertGreater(ch.system_branch_angle(cue + timeline.BEAT), 3.0)
        self.assertGreater(ch.system_branch_angle(timeline.SECTION_END), ch.system_branch_angle(timeline.SECTION_END - 1.0))

    def test_system_branch_releases_within_frames_of_the_hit(self):
        cue = timeline.SYSTEM_DIVERGENCE
        frame = 1.0 / timeline.FPS
        self.assertEqual(ch.system_branch_lift(cue), 0.0)
        # Three frames in: already most of the lift and a visible turn.
        self.assertGreater(ch.system_branch_lift(cue + 3 * frame), 0.14)
        self.assertGreater(ch.system_branch_angle(cue + 3 * frame), 1.8)
        self.assertEqual(ch.system_branch_presence(cue + 3 * frame), 1.0)
        # Six frames in: released. The lift then holds while the slow hinge carries on.
        self.assertAlmostEqual(ch.system_branch_lift(cue + 6 * frame), 0.18)
        self.assertGreater(ch.system_branch_angle(cue + 6 * frame), 2.8)
        self.assertAlmostEqual(ch.system_branch_lift(timeline.SECTION_END), 0.18)
        # The slow divergence is what it was: 9.5 degrees a bar in, 12 at the end.
        self.assertAlmostEqual(ch.system_branch_angle(cue + timeline.BAR), 9.5)
        self.assertAlmostEqual(ch.system_branch_angle(timeline.SECTION_END), 12.0)
        # Restrained: the release never throws the branch backwards or past its swing.
        previous = 0.0
        for i in range(1, 151):
            angle = ch.system_branch_angle(cue + i * frame)
            self.assertGreaterEqual(angle, previous)
            previous = angle

    def test_system_branch_is_the_primary_dependency_elsewhere(self):
        p, b = variants.primary(), variants.system_branch()
        self.assertTrue(b.ghost)
        for field in ("side", "cut_time", "signal_travel", "tower_spin_down", "tower_cells_lost",
                      "tower_head_lift", "tower_head_rotation"):
            self.assertEqual(getattr(p, field), getattr(b, field), field)

    def test_no_cue_time_moved_in_this_pass(self):
        expected = {"alternate_cut": 55.0, "alternate_infrastructure_failure": 57.5, "camera_emphasis": 60.0,
                    "system_divergence": 60.0, "plane_b_retreat_start": 61.25, "primary_cut": 50.0}
        for name, t in expected.items():
            self.assertEqual(timeline.cue(name), t, name)


class PhantomLoadTests(unittest.TestCase):
    """The body acts on a limb it no longer has; the removed piece takes no part."""

    def setUp(self):
        self.a = variants.alternate()
        self.cue = timeline.PHANTOM_LOAD

    def test_nothing_happens_before_the_cue(self):
        a = self.a
        for t in (timeline.SECTION_START, 50.0, 60.0, timeline.SECTION_END, self.cue):
            self.assertEqual(ch.phantom_activation(t), 0.0)
            self.assertEqual(ch.phantom_load(a, t), (0.0, 0.0, 0.0))
            self.assertEqual(ch.conduit_displacement(a, 0.3, t), (0.0, 0.0, 0.0))
            self.assertEqual(ch.tower_lean(a, t), (1.0, 0.0, 0.0, 0.0))
            self.assertEqual(ch.torso_compensation(a, t), (1.0, 0.0, 0.0, 0.0))

    def test_flinch_is_quick_then_the_reach_is_slower(self):
        frame = 1.0 / timeline.FPS
        self.assertGreater(ch.phantom_activation(self.cue + 4 * frame), 0.4)
        self.assertLess(ch.phantom_activation(self.cue + 4 * frame), 0.5)
        self.assertAlmostEqual(ch.phantom_activation(self.cue + 2 * timeline.BEAT), 1.0)

    def test_it_settles_to_a_residue_not_to_neutral(self):
        late = timeline.TIMELINE_END
        residue = ch.phantom_activation(late)
        self.assertGreater(residue, 0.2)
        self.assertLess(residue, 0.35)
        self.assertEqual(residue, ch.phantom_activation(late - 1.0))
        self.assertGreater(length(ch.phantom_load(self.a, late)), 0.1)

    def test_the_load_reaches_the_tower_later_than_the_body(self):
        a, t = self.a, self.cue + 0.5
        self.assertGreater(length(ch.conduit_displacement(a, 0.0, t)), 0.05)
        self.assertEqual(ch.conduit_displacement(a, 1.0, t), (0.0, 0.0, 0.0))
        self.assertEqual(ch.tower_lean(a, t), (1.0, 0.0, 0.0, 0.0))
        self.assertNotEqual(ch.tower_lean(a, self.cue + 2.5), (1.0, 0.0, 0.0, 0.0))

    def test_the_removed_piece_does_not_follow_the_phantom(self):
        a = self.a
        rest = ch.detach_pose(a, a.cut_time + a.detach_duration)
        for dt in (0.0, 0.1, 1.25, 3.0, 6.0):
            self.assertEqual(ch.detach_pose(a, self.cue + dt), rest)

    def test_phantom_chain_keeps_its_bone_lengths(self):
        a = self.a
        upper = layout.arm_elbow_distance()
        fore = layout.arm_length() - upper
        for dt in (0.0, 0.1, 0.7, 1.25, 4.0):
            shoulder, elbow, hand = ch.phantom_chain(a, self.cue + dt)
            self.assertAlmostEqual(length(sub(elbow, shoulder)), upper)
            self.assertAlmostEqual(length(sub(hand, elbow)), fore)

    def test_only_the_alternate_carries_a_phantom(self):
        self.assertTrue(variants.alternate().phantom)
        for v in (variants.primary(), variants.system_branch(), variants.extra_alternate(1)):
            self.assertFalse(v.phantom)
            self.assertEqual(ch.phantom_load(v, self.cue + 1.25), (0.0, 0.0, 0.0))
            self.assertEqual(ch.stump_pose(v, self.cue + 1.25), ch.stump_pose(v, self.cue))

    def test_camera_carries_on_without_a_seam_or_a_new_move(self):
        frame = 1.0 / timeline.FPS
        end = timeline.SECTION_END

        def step(t):
            return length(sub(ch.camera_pose(t + frame)[0], ch.camera_pose(t)[0]))

        self.assertAlmostEqual(step(end - frame), step(end), places=3)
        # ...until the disposal, much later, gives it a new move.
        for i in range(int((timeline.DISPOSAL_TRANSPORT - end) * timeline.FPS)):
            self.assertLessEqual(step(end + i * frame), step(end) + 1e-9)


class HingeTests(unittest.TestCase):
    """1:52.5-2:20: up through the level the chutes hang from, and a hard cut."""

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.core import hinge, landfill
        cls.hinge, cls.field = hinge, landfill

    def test_the_locked_flyover_runs_into_it_without_a_seam(self):
        start = ch.HINGE_START
        self.assertEqual(start, timeline.TIMELINE_END)
        for t in (99.0, 100.0, 105.0, 110.0, 112.4667, start):
            self.assertEqual((ch.hinge_rise(t), ch.hinge_lag(t), ch.hinge_pitch(t)), (0.0, 0.0, 0.0))
            self.assertEqual(ch.lower_camera_pose(t), ch._lower_camera_flyover(t, hinge=False))
        dt = 1.0 / timeline.FPS
        before = sub(ch.lower_camera_pose(start)[0], ch.lower_camera_pose(start - dt)[0])
        after = sub(ch.lower_camera_pose(start + dt)[0], ch.lower_camera_pose(start)[0])
        self.assertLess(length(sub(before, after)), 1e-4)        # under 3 mm/s of change in velocity

    def test_there_are_no_more_disposals(self):
        for event in self.field.events():
            self.assertLess(self.field.event_impact_time(event), ch.HINGE_START)

    def test_the_camera_goes_up_through_the_level_and_on(self):
        hinge = self.hinge
        heights = [ch.lower_camera_pose(ch.HINGE_START + i / 30.0)[0][2] for i in range(0, 676)]
        self.assertEqual(heights, sorted(heights))
        # It reaches the ground of the level between the two cues, after the level has begun to show...
        crossing = ch.HINGE_START + next(i for i, z in enumerate(heights) if z > hinge.GROUND) / 30.0
        self.assertGreater(crossing, hinge.OPEN + 0.5)
        self.assertLess(crossing, hinge.DRAIN - 0.5)
        # ...is a few metres over it on the drain cue, and far above it at the cut.
        self.assertAlmostEqual(ch.lower_camera_pose(hinge.DRAIN)[0][2], -6.8 + 10.8, places=3)
        self.assertGreater(ch.lower_camera_pose(hinge.CUT)[0][2], 160.0)
        # From the drain cue it slows: it is altitude that changes, not ground covered.
        def ground_speed(t):
            a, b = ch.lower_camera_pose(t)[0], ch.lower_camera_pose(t + 0.1)[0]
            return math.hypot(b[0] - a[0], b[1] - a[1]) / 0.1
        self.assertAlmostEqual(ground_speed(119.0), 6.0, delta=0.05)
        self.assertLess(ground_speed(134.8), 1.7)
        # Its path stays a straight line in plan, and it never touches anything on the level.
        for i in range(0, 676, 5):
            position = ch.lower_camera_pose(ch.HINGE_START + i / 30.0)[0]
            self.assertLess(abs(self.field.flight_coordinates(position[0], position[1])[1]), 1e-6)
            for piece in hinge.pieces():
                gap = [max(0.0, abs(position[k] - piece.center[k]) - piece.size[k] * 0.5) for k in range(3)]
                self.assertGreater(math.hypot(*gap), 1.0)

    def test_the_level_is_regular_where_the_chutes_were_not(self):
        hinge = self.hinge
        pieces = hinge.pieces()
        trunks = sorted({round(piece.center[0], 6) for piece in pieces if piece.kind == "trunk"})
        gaps = {round(b - a, 6) for a, b in zip(trunks, trunks[1:])}
        self.assertEqual(gaps, {24.0})                                   # parallel and evenly spaced
        self.assertEqual({round(piece.size[0], 6) for piece in pieces if piece.kind == "trunk"}, {1.6, 4.0})
        # A hierarchy of widths: fine local runs, trunks, mains, and one heavy bus each way.
        fine = {round(min(piece.size[:2]), 6) for piece in pieces if piece.kind == "fine"}
        main_widths = {round(piece.size[1], 6) for piece in pieces if piece.kind == "main"}
        self.assertEqual((fine, main_widths), ({0.6}, {2.6, 5.0}))
        self.assertGreater(sum(piece.kind == "fine" for piece in pieces), 100)
        self.assertGreater(sum(piece.kind == "cell" for piece in pieces), 100)
        self.assertGreater(sum(piece.kind == "via" for piece in pieces), 200)
        # Everything runs along the grid's two axes; the finest layer is lower than what it runs between.
        self.assertLess(max(piece.size[2] for piece in pieces if piece.kind == "fine"), 0.75)
        # What was there before the refinement comes first and is unchanged in number.
        self.assertEqual([piece.kind for piece in pieces[:871]].count("trunk"), 289)
        self.assertEqual({piece.kind for piece in pieces[871:]}, {"via", "bay", "fine", "cell"})
        mains = sorted({round(piece.center[1], 6) for piece in pieces if piece.kind == "main"})
        self.assertEqual({round(b - a, 6) for a, b in zip(mains, mains[1:])}, {96.0})
        # Every station is a unit square to the grid, joined to its own trunk by a spur.
        stations = self.field.stations()
        units = {piece.station: piece for piece in pieces if piece.kind == "unit"}
        spurs = {piece.station: piece for piece in pieces if piece.kind == "spur"}
        self.assertGreater(len(units), 250)
        for index, unit in units.items():
            self.assertAlmostEqual(unit.center[0], stations[index].x)
            self.assertAlmostEqual(unit.center[1], stations[index].y)
            spur = spurs[index]
            ends = (spur.center[0] - spur.size[0] * 0.5, spur.center[0] + spur.size[0] * 0.5)
            self.assertTrue(any(abs(end - hinge.column_x(unit.column)) < 1e-6 for end in ends))
            self.assertLessEqual(spur.size[0], 8.5 + 1e-6)
        # The stations themselves are not regular: that is what the level reveals about them.
        offsets = [abs(stations[index].x - hinge.column_x(unit.column)) for index, unit in units.items()]
        self.assertGreater(max(offsets), 7.0)

    def test_none_of_it_can_be_seen_before_the_hinge(self):
        hinge = self.hinge
        for piece in hinge.pieces():
            # Above the pit's ceiling, and clear of the chamber that stands on the same level.
            self.assertGreaterEqual(piece.center[2] - piece.size[2] * 0.5, hinge.GROUND - 1e-9)
            inside_x = abs(piece.center[0]) - piece.size[0] * 0.5 < layout.CHAMBER_HALF_WIDTH + 2.0
            inside_y = (layout.CHAMBER_Y_MIN - 2.0 < piece.center[1] + piece.size[1] * 0.5
                        and piece.center[1] - piece.size[1] * 0.5 < layout.CHAMBER_Y_MAX + 2.0)
            self.assertFalse(inside_x and inside_y)
        sample = hinge.pieces()[::37]
        for t in (0.0, 35.0, 96.9, 110.0, 112.5, hinge.OPEN):
            self.assertTrue(hinge.ceiling_present(t) or t == hinge.OPEN)
            for piece in sample:
                self.assertEqual(hinge.visibility(piece, t), 0.0)
        self.assertTrue(hinge.ceiling_present(hinge.OPEN - 1.0 / 30.0))
        self.assertFalse(hinge.ceiling_present(hinge.DRAIN))

    def test_the_cut_leaves_one_axis_and_one_station(self):
        hinge = self.hinge
        self.assertEqual([ch.which_camera(t) for t in (35.0, 96.9, 112.5, 134.9667, 135.0, 139.9, 255.0, 265.0)],
                         ["upper", "lower", "lower", "lower", "hinge", "hinge", "hinge", "upper"])
        self.assertTrue(hinge.ceiling_present(hinge.CUT))
        for t in (hinge.CUT, 137.0, hinge.END):
            lit = [piece for piece in hinge.pieces() if hinge.visibility(piece, t) > 0.0]
            self.assertEqual({piece.column for piece in lit}, {hinge._axis()[0]})
            self.assertEqual({piece.station for piece in lit if piece.kind != "trunk"}, {hinge._axis()[1]})
            self.assertEqual(sorted({piece.kind for piece in lit}), ["spur", "trunk", "unit"])
        # The camera stands still, and looks along the trunk it is beside.
        position, rotation, fov = hinge.still_camera()
        self.assertEqual(hinge.still_camera(), (position, rotation, fov))
        self.assertLess(abs(position[0] - hinge.column_x(hinge._axis()[0])), 7.0)
        forward = q_rotate(rotation, (0.0, 0.0, -1.0))
        self.assertGreater(forward[1], 0.99)
        # The chamber is behind it.
        self.assertGreater(position[1], layout.CHAMBER_Y_MAX + 30.0)

    def test_the_ending_is_as_it_was_locked(self):
        for t in (265.0, 272.0, 280.0):
            self.assertEqual(ch.lower_camera_pose(t), ch._lower_camera_flyover(t, hinge=False))
            self.assertTrue(self.hinge.ceiling_present(t))


class RefrainTests(unittest.TestCase):
    """2:20-3:00: the system without a subject, seen from inside."""

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.core import hinge, landfill, refrain
        cls.hinge, cls.field, cls.refrain = hinge, landfill, refrain

    def test_it_starts_from_exactly_the_state_the_hinge_left(self):
        hinge, refrain = self.hinge, self.refrain
        self.assertEqual((refrain.START, refrain.PROCEDURE, refrain.END), (140.0, 160.0, 180.0))
        for t in (135.0, 138.0, 140.0):
            self.assertEqual(refrain.camera_pose(t), hinge.still_camera())
            self.assertEqual(refrain.sight(t), 0.0)
            self.assertEqual(refrain.coupling(t), 0.0)
            self.assertEqual(refrain.rotor_angle(t), 0.0)
            for kit in refrain.kits():
                self.assertEqual(refrain.seen((kit.x, kit.y, 0.0), t), 0.0)
                self.assertEqual((refrain.carriage(kit, t), refrain.yoke_drop(kit, t)), ((0.0, 0.0), 0.0))
            for piece in hinge.pieces()[::29]:
                self.assertEqual(hinge.visibility(piece, t), hinge._left_after_cut(piece))
        # It leaves from rest.
        step = length(sub(refrain.camera_position(140.0 + 1.0 / 30.0), refrain.camera_position(140.0)))
        self.assertLess(step, 1e-4)

    def test_the_camera_travels_the_trunk_at_station_height(self):
        refrain = self.refrain
        previous = refrain.camera_position(140.0)
        for i in range(1, 1201):
            position = refrain.camera_position(140.0 + i / 30.0)
            self.assertGreaterEqual(position[1], previous[1])                 # always forward
            self.assertLess(length(sub(position, previous)), 0.125)           # never above 3.75 m/s
            self.assertLess(position[2], self.hinge.GROUND + 8.0)             # never a flyover
            previous = position
        # Slow while it observes, quicker once the stations are working.
        self.assertAlmostEqual(refrain.camera_travel(160.0) - refrain.camera_travel(159.0), 2.0, places=6)
        self.assertAlmostEqual(refrain.camera_travel(180.0) - refrain.camera_travel(179.0), 3.6, places=6)
        # It never touches the level or anything standing on a station.
        for i in range(0, 1201, 6):
            position = refrain.camera_position(140.0 + i / 30.0)
            for piece in self.hinge.pieces():
                gap = [max(0.0, abs(position[k] - piece.center[k]) - piece.size[k] * 0.5) for k in range(3)]
                self.assertGreater(math.hypot(*gap), 1.5)
            for kit in refrain.kits():
                gap = (max(0.0, abs(position[0] - kit.x) - 4.0), max(0.0, abs(position[1] - kit.y) - 4.0),
                       max(0.0, position[2] - (refrain.TOP + 4.6)))
                self.assertGreater(math.hypot(*gap), 1.5)

    def test_the_level_comes_out_of_the_dark_as_the_camera_reaches_it(self):
        refrain = self.refrain

        def visible(t):
            return sum(1 for kit in refrain.kits() if refrain.seen((kit.x, kit.y, 0.0), t) > 0.3)

        counts = [visible(t) for t in (140.0, 145.0, 150.0, 160.0, 170.0, 180.0)]
        self.assertEqual(counts[0], 0)
        self.assertEqual(counts, sorted(counts))
        self.assertLess(counts[1], 6)
        self.assertGreater(counts[-1], 25)
        # What it has passed goes dark again behind it: sight is a distance, not a switch.
        behind = (refrain.camera_position(180.0)[0], refrain.camera_position(180.0)[1] - 160.0, 0.0)
        self.assertEqual(refrain.seen(behind, 180.0), 0.0)

    def test_it_couples_at_two_twenty_without_a_body(self):
        refrain = self.refrain
        self.assertEqual(refrain.coupling(144.0), 1.0)
        previous = refrain.clock(140.0)
        for i in range(1, 150):
            now = refrain.clock(140.0 + i / 30.0)
            self.assertGreater(now, previous)
            previous = now
        self.assertAlmostEqual(refrain.clock(150.0) - refrain.clock(149.0), 1.0)
        # One blade a beat, as the chamber's rotors turn.
        self.assertAlmostEqual(refrain.rotor_angle(150.0 + timeline.BEAT) - refrain.rotor_angle(150.0), 60.0)
        self.assertEqual(outer.subject_presence(150.0), 1.0)        # the hinge camera never sees the chamber

    def test_the_procedure_passes_from_station_to_station(self):
        refrain = self.refrain
        kits = refrain.kits()
        self.assertGreater(len(kits), 25)
        begins = sorted(kit.begins for kit in kits)
        self.assertEqual(begins[0], refrain.PROCEDURE)                # the first starts on the cue
        self.assertEqual([kit.station for kit in kits if kit.begins == refrain.PROCEDURE], [131])
        self.assertLess(begins[-1], refrain.END - 2.0)                # all are running by 3:00
        self.assertGreater(len(set(begins)), 12)                      # and they do not start together
        for kit in kits:
            beats = (kit.begins - refrain.PROCEDURE) / timeline.BEAT
            self.assertAlmostEqual(beats, round(beats), places=6)     # each on a beat
            # Nothing before its turn.
            self.assertEqual((refrain.carriage(kit, kit.begins), refrain.yoke_drop(kit, kit.begins)), ((0.0, 0.0), 0.0))
            # One run takes three bars and returns exactly to rest, so it repeats without a seam.
            end = kit.begins + refrain.PERIOD - 1e-6
            if end < refrain.END:
                self.assertAlmostEqual(refrain.head_yaw(kit, end), refrain.head_yaw(kit, kit.begins), places=3)
                self.assertAlmostEqual(refrain.carriage(kit, end)[0], 0.0, places=6)
                self.assertAlmostEqual(refrain.yoke_drop(kit, end), 0.0, places=6)
        # It is not still at 3:00: stations are in mid-procedure.
        moving = sum(1 for kit in kits
                     if abs(refrain.head_yaw(kit, 180.0) - refrain.head_yaw(kit, 179.9)) > 0.01
                     or abs(refrain.carriage(kit, 180.0)[0] - refrain.carriage(kit, 179.9)[0]) > 1e-4
                     or abs(refrain.yoke_drop(kit, 180.0) - refrain.yoke_drop(kit, 179.9)) > 1e-4)
        self.assertGreater(moving, 8)

    def test_every_station_works_around_an_empty_coordinate(self):
        refrain = self.refrain
        for kit in refrain.kits():
            empty = refrain.empty_coordinate(kit)
            hx, hy = kit.x + kit.front * refrain.HEAD_AT[0], kit.y + refrain.HEAD_AT[1]
            # The head turns to face it: the same 86.5 degrees the chamber's tower head turned at 0:02.
            t = kit.begins + 1.4
            facing = q_rotate(q_axis_angle_z(refrain.head_yaw(kit, t)), (0.0, -1.0, 0.0))
            toward = normalize((empty[0] - hx, empty[1] - hy, 0.0))
            self.assertAlmostEqual(dot(facing, toward), 1.0, places=6)
            self.assertAlmostEqual(abs(refrain.head_yaw(kit, t) - refrain.head_yaw(kit, kit.begins)), 86.5, places=6)
            # The yoke comes down toward it and stops short.
            lowest = refrain.TOP + refrain.YOKE_HEIGHT - 0.24 - max(refrain.yoke_drop(kit, kit.begins + k / 10.0) for k in range(75))
            self.assertGreater(lowest, empty[2] + 0.1)
            # The carriage runs toward the platform's line and does not reach it.
            self.assertLess(abs(refrain.CARRIAGE_HOME) - max(refrain.carriage(kit, kit.begins + k / 10.0)[0] for k in range(75)), 1.5)
            self.assertGreater(abs(refrain.CARRIAGE_HOME) - 1.6, 0.9)

    def test_scrawls_wander_and_bars_are_ranked(self):
        refrain = self.refrain
        marks = refrain.marks()
        self.assertEqual(marks, refrain.marks())
        scrawls = [m for m in marks if m.kind == "scrawl"]
        bars = [m for m in marks if m.kind == "bar"]
        self.assertGreater(len(scrawls), 200)
        self.assertGreater(len(bars), 100)
        self.assertLess(len(marks), 1200)                                # the minimum that reads
        # Bars: one size on faces and one on tops, all square to the station, in rows.
        self.assertEqual(len({m.size for m in bars}), 2)
        self.assertEqual({m.rotation for m in bars}, {(1.0, 0.0, 0.0, 0.0)})
        rows = {}
        for m in bars:
            rows.setdefault((round(m.center[0], 3), round(m.center[2], 3)), []).append(m.center[1])
        faces = {}
        for (x, z), ys in rows.items():
            faces.setdefault(x, []).append((z, len(ys), min(ys)))
        for x, face in faces.items():
            face.sort(reverse=True)                                       # from the top row down
            counts = [count for _, count, _ in face]
            self.assertEqual(counts, sorted(counts, reverse=True))        # ranked: never longer below
            self.assertEqual(len({round(left, 6) for _, _, left in face}), 1)   # squared up at one end
        # Scrawls: many different angles, no two strokes alike.
        angles = {round(2.0 * math.degrees(math.acos(min(1.0, abs(m.rotation[0])))), 0) for m in scrawls}
        self.assertGreater(len(angles), 40)
        # The station the hinge left lit carries neither.
        lit = self.field.stations()[131]
        for m in bars + [m for m in scrawls if m.center[2] > self.hinge.GROUND + 0.2]:
            self.assertGreater(math.hypot(m.center[0] - lit.x, m.center[1] - lit.y), 6.0)

    def test_the_state_at_three_minutes(self):
        refrain = self.refrain
        position, rotation, fov = refrain.camera_pose(180.0)
        forward = q_rotate(rotation, (0.0, 0.0, -1.0))
        self.assertGreater(forward[0], 0.5)                       # turned toward the heavy main, to the east
        self.assertGreater(forward[1], 0.2)                       # and not yet all the way
        bus = self.hinge.row_y(self.hinge.BUS_MAIN_ROW)
        self.assertLess(bus - position[1], 15.0)
        self.assertGreater(bus - position[1], 5.0)
        ahead = sum(1 for kit in refrain.kits()
                    if refrain.seen((kit.x, kit.y, 0.0), 180.0) > 0.3 and kit.x > position[0])
        self.assertGreater(ahead, 12)


class NetworkTests(unittest.TestCase):
    """3:00-3:30: one system, and then the absence it is organised around."""

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.core import hinge, landfill, network, refrain
        cls.hinge, cls.field, cls.network, cls.refrain = hinge, landfill, network, refrain
        cls.kits = refrain.kits() + refrain.later_kits()

    def test_it_leaves_three_minutes_exactly_as_the_refrain_arrives(self):
        network, refrain = self.network, self.refrain
        self.assertEqual((network.START, network.RESPONSE, network.RELEASE, network.VOID, network.END),
                         (180.0, 187.5, 195.0, 200.0, 210.0))
        # At 3:00.0 everything is the refrain's own state...
        self.assertEqual(network.camera_position(180.0), refrain.camera_position(180.0))
        for kit in refrain.kits():
            self.assertEqual(network.phase(kit, 180.0), refrain._phase(kit, 180.0))
            self.assertAlmostEqual(network.head_yaw(kit, 180.0), refrain.head_yaw(kit, 180.0), places=9)
            for now, then in zip(network.carriage(kit, 180.0), refrain.carriage(kit, 180.0)):
                self.assertAlmostEqual(now, then, places=12)
            self.assertAlmostEqual(network.yoke_drop(kit, 180.0), refrain.yoke_drop(kit, 180.0), places=12)
        for piece in self.hinge.pieces()[::17]:
            self.assertEqual(network.piece_offset(piece, 180.0), (0.0, 0.0, 0.0))
        self.assertEqual(network.arrival(180.0), 0.0)
        # ...and the camera goes on at the speed and with the turn it had.
        dt = 1.0 / timeline.FPS
        before = sub(refrain.camera_position(180.0), refrain.camera_position(180.0 - dt))
        after = sub(refrain.camera_position(180.0 + dt), refrain.camera_position(180.0))
        self.assertLess(length(sub(before, after)), 0.002)
        def turned(a, b):
            return math.degrees(2.0 * math.acos(min(1.0, abs(sum(x * y for x, y in zip(a, b))))))
        r0, r1, r2 = (refrain.camera_pose(180.0 + k * dt)[1] for k in (-1, 0, 1))
        self.assertAlmostEqual(turned(r0, r1), turned(r1, r2), delta=0.01)

    def test_the_camera_crosses_the_network_and_enters_the_lane(self):
        network, refrain = self.network, self.refrain
        previous = refrain.camera_position(180.0)
        for i in range(1, 901):
            position = refrain.camera_position(180.0 + i / 30.0)
            self.assertLess(length(sub(position, previous)), 0.2)                  # never above 6 m/s
            # Inside the machine, not over it: between 5 and 13 m above the level throughout.
            self.assertTrue(5.0 < position[2] - self.hinge.GROUND < 13.0)
            previous = position
        # By 3:20 it is on the lane's axis, and it stays on it.
        for t in (200.0, 203.0, 206.0, 210.0):
            position = refrain.camera_position(t)
            self.assertLess(abs(network.lane_coordinates(position[0], position[1])[1]), 1.2)
        along = [network.lane_coordinates(*refrain.camera_position(t)[:2])[0] for t in (200.0, 205.0, 210.0)]
        self.assertEqual(along, sorted(along))
        self.assertLess(along[-1], network.LANE_LENGTH)                            # still inside it at 3:30
        # It is still moving at 3:30.
        self.assertGreater(length(sub(refrain.camera_position(210.0), refrain.camera_position(209.9))), 0.5)
        # It never touches the level or anything standing on a station.
        for i in range(0, 901, 5):
            position = refrain.camera_position(180.0 + i / 30.0)
            for piece in self.hinge.pieces():
                gap = [max(0.0, abs(position[k] - piece.center[k]) - piece.size[k] * 0.5) for k in range(3)]
                self.assertGreater(math.hypot(*gap), 3.0)
            for kit in self.kits:
                gap = (max(0.0, abs(position[0] - kit.x) - 4.0), max(0.0, abs(position[1] - kit.y) - 4.0),
                       max(0.0, position[2] - (refrain.TOP + 4.6)))
                self.assertGreater(math.hypot(*gap), 3.0)

    def test_it_looks_down_while_the_lane_lasts_and_up_as_it_runs_out(self):
        network, refrain = self.network, self.refrain

        def pitch(t):
            forward = q_rotate(refrain.camera_pose(t)[1], (0.0, 0.0, -1.0))
            return -math.degrees(math.asin(forward[2]))

        # Up to 3:20.0 its gaze is what it was.
        for t, was in ((195.0, 11.0), (198.0, 10.616), (200.0, 10.0)):
            self.assertAlmostEqual(pitch(t), was, places=5)
        for t in (201.0, 202.5, 204.0, 205.5, 207.0):
            self.assertTrue(9.5 <= pitch(t) <= 10.01, (t, pitch(t)))
        lifting = [pitch(t) for t in (207.0, 208.0, 209.0, 210.0)]
        self.assertEqual(lifting, sorted(lifting, reverse=True))
        self.assertAlmostEqual(pitch(210.0), 5.0, places=5)
        self.assertGreater(pitch(209.9) - pitch(210.0), 0.05)              # still lifting at 3:30

    def test_the_lane_is_empty_and_was_not_built(self):
        network = self.network
        # No station, and nothing belonging to one, stands within the lane's width.
        for index, station in enumerate(self.field.stations()):
            bayed = stablehash.value(timeline.SEED + 52000, index) < 0.38
            half_y = 10.8 if bayed else 4.0                            # a unit, and its bays if it has them
            for k in range(61):
                x, y = network.lane_point(network.LANE_LENGTH * k / 60.0)
                gap = math.hypot(max(0.0, abs(x - station.x) - 4.0), max(0.0, abs(y - station.y) - half_y))
                self.assertGreater(gap, network.LANE_HALF_WIDTH - 1.5, index)
        # What does lie across it is low routing only.
        for piece in self.hinge.pieces():
            if network.lane_distance(piece.center[0], piece.center[1]) < 3.0:
                self.assertIn(piece.kind, ("cell", "trunk", "fine"))
                self.assertLess(piece.size[2], 1.6)

    def test_stations_fall_into_step_ring_by_ring(self):
        network, refrain = self.network, self.refrain
        period = refrain.PERIOD
        for kit in self.kits:
            # Never backward, and never more than a little faster than the clock.
            previous = network.phase(kit, 180.0)
            for i in range(1, 600):
                now = network.phase(kit, 180.0 + i / 30.0)
                if now is not None and previous is not None:
                    step = (now - previous) % period
                    self.assertTrue(0.0 < step < 0.08, (kit.station, step))
                previous = now
        # By 3:17 every ring is one phase, on a bar line, and rings stand a bar apart.
        by_ring = {}
        for kit in self.kits:
            by_ring.setdefault(network.ring(kit), set()).add(round(network.phase(kit, 197.0), 6))
        self.assertGreater(len(by_ring), 3)
        for phases in by_ring.values():
            self.assertEqual(len(phases), 1)
        phases = {ring: next(iter(p)) for ring, p in by_ring.items()}
        for ring, phase in phases.items():
            self.assertAlmostEqual((197.0 - 180.0 - (ring % 3) * timeline.BAR) % period, phase, places=5)
        self.assertEqual(len(set(phases.values())), 3)
        # It spreads: the ring at the junction locks first.
        self.assertEqual(network.locked(min(self.kits, key=network.ring), 188.0), 1.0)
        self.assertLess(network.locked(max(self.kits, key=network.ring), 188.0), 0.7)
        # At 3:00 they were not in step.
        self.assertGreater(len({round(refrain._phase(kit, 180.0), 3) for kit in refrain.kits()}), 8)

    def test_large_structures_take_part(self):
        network = self.network
        moving = [piece for piece in self.hinge.pieces() if network.moves(piece)]
        kinds = {piece.kind for piece in moving}
        self.assertEqual(kinds, {"cell", "main", "trunk", "fine"})
        self.assertLess(len(moving), 80)                                    # not the whole grid
        array = [piece for piece in moving if network._in_array(piece)]
        main = [piece for piece in moving if network._risen_main(piece)]
        self.assertGreater(len(array), 40)
        self.assertEqual(len(main), 5)
        clear = [piece for piece in array if not network._across_lane(piece)]
        # The array goes down on the response cue and is back after the release.
        self.assertEqual({network.piece_offset(piece, 187.5)[2] for piece in clear}, {0.0})
        self.assertEqual({round(network.piece_offset(piece, 190.0)[2], 6) for piece in clear}, {-0.45})
        self.assertEqual({round(network.piece_offset(piece, 198.0)[2], 6) for piece in clear}, {0.0})
        # The main rises half a bar later.
        self.assertEqual({network.piece_offset(piece, 188.75)[2] for piece in main}, {0.0})
        self.assertEqual({round(network.piece_offset(piece, 191.0)[2], 6) for piece in main}, {0.8})
        self.assertEqual({round(network.piece_offset(piece, 199.0)[2], 6) for piece in main}, {0.0})

    def test_at_three_twenty_the_network_turns_to_the_lane(self):
        network, refrain = self.network, self.refrain
        beside = [kit for kit in self.kits if network.beside_lane(kit)]
        away = [kit for kit in self.kits if not network.beside_lane(kit)]
        self.assertGreater(len(beside), 10)
        self.assertGreater(len(away), 10)
        for kit in self.kits:
            self.assertEqual(network.held(kit, 200.0), 0.0)                 # nothing before the bass leaves
        for kit in beside:
            self.assertEqual(network.held(kit, 206.0), 1.0)
            # Its head faces the lane, not its own platform...
            hx, hy = kit.x + kit.front * refrain.HEAD_AT[0], kit.y + refrain.HEAD_AT[1]
            facing = q_rotate(q_axis_angle_z(network.head_yaw(kit, 208.0)), (0.0, -1.0, 0.0))
            along = min(max(network.lane_coordinates(hx, hy)[0], 0.0), network.LANE_LENGTH)
            px, py = network.lane_point(along)
            self.assertAlmostEqual(dot(facing, normalize((px - hx, py - hy, 0.0))), 1.0, places=6)
            # ...and its procedure is held short of its end, not reset: nothing is back at rest.
            self.assertEqual(network.carriage(kit, 208.0), network.carriage(kit, 210.0))
            self.assertAlmostEqual(network.carriage(kit, 210.0)[0], 0.8)
            self.assertAlmostEqual(network.yoke_drop(kit, 210.0), 0.3)
            self.assertLess(network.yoke_drop(kit, 210.0), refrain.YOKE_DROP)
        # Stations away from the lane go on, but no longer reach the end of their strokes.
        for kit in away:
            self.assertEqual(network.held(kit, 210.0), 0.0)
            reach = max(network.yoke_drop(kit, 203.0 + i / 10.0) for i in range(70))
            self.assertLess(reach, 0.45 * refrain.YOKE_DROP)
        # What lies across the lane withdraws; nothing rises into it.
        across = [piece for piece in self.hinge.pieces() if network._across_lane(piece)]
        self.assertGreater(len(across), 8)
        for piece in across:
            self.assertEqual(network.piece_offset(piece, 200.0)[2], network.piece_offset(piece, 199.0)[2])
            # Each goes down by more than its own height: the ground closes over it, no stub.
            self.assertLess(network.piece_offset(piece, 210.0)[2], -piece.size[2])
            self.assertIn(piece.kind, ("cell", "trunk", "fine", "main"))
        # They go band by band down the lane, each on a beat or half-beat, always ahead of the camera.
        times = sorted({network.clearing_time(piece) for piece in across})
        self.assertEqual(times[0], 200.0)
        self.assertGreater(len(times), 8)
        self.assertGreater(times[-1], 207.5)                       # still clearing ahead late in the passage
        self.assertLess(times[-1] + 1.2, 210.0)
        for t in times:
            self.assertAlmostEqual((t - 200.0) / (timeline.BEAT * 0.5), round((t - 200.0) / (timeline.BEAT * 0.5)), places=6)
        ordered = sorted(across, key=network.intrusion)
        self.assertEqual([network.clearing_time(p) for p in ordered], sorted(network.clearing_time(p) for p in ordered))
        for piece in across:
            if network.intrusion(piece) < 12.0:
                continue                                           # under the camera as it comes down into the lane
            down = network.clearing_time(piece) + 1.2
            arrives = next(200.0 + i / 30.0 for i in range(400)
                           if network.lane_coordinates(*refrain.camera_position(200.0 + i / 30.0)[:2])[0] >= network.intrusion(piece)
                           or i == 399)
            self.assertGreater(arrives - down, 0.5)
        # A length of the heavy main is the largest thing that goes.
        self.assertEqual(sum(1 for piece in across if piece.kind == "main"), 1)
        # A few of the nearest stations on each side turn their whole overhead frames, all the same way.
        flanking = network.flanking()
        self.assertTrue(6 <= len(flanking) <= 8)
        self.assertEqual(len(set(flanking.values())), len(flanking))        # never two at once
        by_station = {kit.station: kit for kit in self.kits}
        sides = [network.lane_coordinates(by_station[s].x, by_station[s].y)[1] > 0 for s in flanking]
        self.assertTrue(3 <= sum(sides) <= 4 and 3 <= len(sides) - sum(sides) <= 4)
        for station, begins in flanking.items():
            kit = by_station[station]
            self.assertTrue(network.beside_lane(kit))
            self.assertGreaterEqual(begins, 200.625)
            self.assertEqual(network.gantry_yaw(kit, begins), 0.0)
            self.assertAlmostEqual(network.gantry_yaw(kit, 210.0), -12.0, delta=0.01)   # the last is just arriving
            # No part of a frame, however turned, comes inside the lane.
            self.assertGreater(abs(network.lane_coordinates(kit.x, kit.y)[1]) - 2.9, network.LANE_HALF_WIDTH)
        for kit in self.kits:
            if kit.station not in flanking:
                self.assertEqual(network.gantry_yaw(kit, 210.0), 0.0)
            self.assertEqual(network.gantry_yaw(kit, 200.0), 0.0)
        for piece in self.hinge.pieces():
            if network.lane_distance(piece.center[0], piece.center[1]) < network.LANE_HALF_WIDTH:
                self.assertLessEqual(network.piece_offset(piece, 210.0)[2], 0.0)

    def test_stations_built_for_this_passage_were_plain_until_three_minutes(self):
        network, refrain = self.network, self.refrain
        self.assertGreater(len(refrain.later_kits()), 5)
        self.assertFalse({kit.station for kit in refrain.later_kits()} & {kit.station for kit in refrain.kits()})
        self.assertEqual(network.arrival(180.0), 0.0)
        self.assertEqual(network.arrival(186.0), 1.0)
        # The refrain's own stations and marks are exactly what they were.
        self.assertEqual(len(refrain.kits()), 31)
        self.assertEqual(len(refrain.marks()), 841)


class ProsthesisTests(unittest.TestCase):
    """3:30-4:00: the network routes function round the absence."""

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.core import hinge, landfill, network, prosthesis, refrain
        cls.hinge, cls.field, cls.network, cls.prosthesis, cls.refrain = hinge, landfill, network, prosthesis, refrain
        cls.kits = {kit.station: kit for kit in refrain.kits() + refrain.later_kits()}

    def state(self, kit, t):
        r = self.refrain
        return r.head_yaw(kit, t), r.carriage(kit, t), r.yoke_drop(kit, t)

    def test_it_starts_from_exactly_the_locked_state(self):
        network, prosthesis, refrain = self.network, self.prosthesis, self.refrain
        self.assertEqual((prosthesis.START, prosthesis.SEED, prosthesis.RELAY, prosthesis.DETOUR, prosthesis.WIDEN, prosthesis.END),
                         (210.0, 211.25, 213.75, 220.0, 230.0, 240.0))
        self.assertEqual(refrain.camera_pose(210.0), network.camera_pose(210.0))
        for kit in self.kits.values():
            self.assertEqual(self.state(kit, 210.0), (network.base_head_yaw(kit, 210.0), network.base_carriage(kit, 210.0),
                                                      network.base_yoke_drop(kit, 210.0)))
            # Nothing is recruited until the first bass hit.
            self.assertEqual(prosthesis.recruited(kit.station, 211.2), 0.0)
            self.assertEqual(self.state(kit, 211.0), (network.base_head_yaw(kit, 211.0), network.base_carriage(kit, 211.0),
                                                      network.base_yoke_drop(kit, 211.0)))
        for piece in self.hinge.pieces()[::13]:
            self.assertEqual(prosthesis.piece_offset(piece, 210.0), (0.0, 0.0, 0.0))
        dt = 1.0 / timeline.FPS
        before = sub(refrain.camera_position(210.0), refrain.camera_position(210.0 - dt))
        after = sub(refrain.camera_position(210.0 + dt), refrain.camera_position(210.0))
        self.assertLess(length(sub(before, after)), 0.002)

    def test_station_237_keeps_the_lane_and_takes_a_second_relation(self):
        network, prosthesis, refrain = self.network, self.prosthesis, self.refrain
        kit = self.kits[237]
        self.assertEqual(network.held(kit, 210.0), 1.0)                    # it already faces the lane
        self.assertEqual(prosthesis.recruits()[237][:2], ("donor", 211.25))
        to_lane = network.base_head_yaw(kit, 215.0)
        block = self.field.stations()[224]
        hx, hy = kit.x + kit.front * refrain.HEAD_AT[0], kit.y + refrain.HEAD_AT[1]
        to_block = math.degrees(math.atan2(block.x - hx, hy - block.y))
        # Each turn its head goes to the block and comes back to the lane.
        self.assertAlmostEqual((refrain.head_yaw(kit, 211.25 + 7.5 + 2.0) - to_block + 180.0) % 360.0 - 180.0, 0.0, places=3)
        self.assertAlmostEqual(refrain.head_yaw(kit, 211.25 + 7.5 + 5.0), to_lane, places=6)
        # Its yoke and carriage stay as the lane left them: that relation is kept.
        for t in (212.0, 220.0, 239.0):
            self.assertAlmostEqual(refrain.yoke_drop(kit, t), 0.3)
            self.assertAlmostEqual(refrain.carriage(kit, t)[0], 0.8)

    def test_station_224_is_a_block_that_indexes(self):
        prosthesis = self.prosthesis
        self.assertNotIn(224, self.kits)                                   # it has no machinery, and gets none
        parts = [piece for piece in self.hinge.pieces() if piece.station == 224 and prosthesis.moves(piece)]
        self.assertEqual(sorted(piece.kind for piece in parts), ["spur", "unit"])
        for piece in parts:
            # It starts a beat after station 237's head and is done while it is still in the picture.
            self.assertEqual(prosthesis.RELAY_BEGINS, 211.875)
            self.assertEqual(prosthesis.piece_offset(piece, 211.875), (0.0, 0.0, 0.0))
            self.assertAlmostEqual(prosthesis.piece_offset(piece, 213.075)[1], 1.6)
            self.assertAlmostEqual(prosthesis.piece_offset(piece, 216.0)[1], 1.6)
            self.assertAlmostEqual(prosthesis.piece_offset(piece, 240.0)[1], 2.6)
            self.assertEqual(prosthesis.piece_offset(piece, 240.0)[0::2], (0.0, 0.0))

    def test_function_is_divided_along_a_path_round_the_lane(self):
        network, prosthesis, refrain = self.network, self.prosthesis, self.refrain
        recruits = prosthesis.recruits()
        roles = [role for _, role, _ in prosthesis.PATH]
        self.assertEqual(set(roles), {"donor", "carrier", "receiver"})
        for first, second, third in zip(roles, roles[1:], roles[2:]):
            self.assertEqual(len({first, second, third}), 3)               # donor, carrier, receiver, in turn
        # The path goes round the lane's end and never through the lane.
        stations = self.field.stations()
        sides = [network.lane_coordinates(stations[s].x, stations[s].y)[1] > 0 for s, _, _ in prosthesis.PATH]
        self.assertEqual(sides, sorted(sides, reverse=True))               # one bank, then the other
        self.assertTrue(any(sides) and not all(sides))
        for (a, _, _), (b, _, _) in zip(prosthesis.PATH, prosthesis.PATH[1:]):
            for k in range(21):
                x = stations[a].x + (stations[b].x - stations[a].x) * k / 20.0
                y = stations[a].y + (stations[b].y - stations[a].y) * k / 20.0
                along, across = network.lane_coordinates(x, y)
                self.assertFalse(0.0 <= along <= network.LANE_LENGTH and abs(across) < network.LANE_HALF_WIDTH, (a, b))
        # It grows: a few by 3:40, more by 3:50, more again by 4:00, and faster at the end.
        def count(t):
            return sum(1 for _, when, _ in recruits.values() if when <= t) + (1 if prosthesis.RELAY <= t else 0)
        self.assertEqual((count(211.25), count(220.0), count(230.0), count(240.0)), (1, 4, 10, 13))
        # Recruitment goes outward from station 237 along each bank, never out of order, and
        # the north bank is finished before the south bank begins.
        whens = [recruits[station][1] for station, _, _ in prosthesis.PATH]
        seed = [station for station, _, _ in prosthesis.PATH].index(237)
        north, south = whens[:seed][::-1], whens[seed + 1:]
        self.assertEqual(north, sorted(north))
        self.assertEqual(south, sorted(south))
        self.assertTrue(whens[seed] < prosthesis.RELAY_BEGINS < north[0] <= north[-1] < south[0])
        # Every recruitment is on the beat grid.
        for when in whens:
            self.assertAlmostEqual((when - 210.0) / timeline.BEAT, round((when - 210.0) / timeline.BEAT), places=6)
        # There are holds: nothing is handed on for more than two bars before each bank starts.
        self.assertGreater(north[0] - (prosthesis.RELAY_BEGINS + prosthesis.RELAY_STROKE), 3.0)
        self.assertGreater(south[0] - north[-1], 3.0)
        # A recruited station does one part completely and leaves the other two as they were.
        for station, (role, when, _) in recruits.items():
            kit = self.kits[station]
            if when + 1.5 > 240.0:
                continue
            reach = [self.state(kit, when + i / 10.0) for i in range(min(76, int((240.0 - when) * 10)))]
            base = [(network.base_head_yaw(kit, when + i / 10.0), network.base_carriage(kit, when + i / 10.0),
                     network.base_yoke_drop(kit, when + i / 10.0)) for i in range(len(reach))]
            if role == "carrier":
                self.assertAlmostEqual(max(c[0] for _, c, _ in reach), 2.4, places=2)
                self.assertAlmostEqual(max(c[1] for _, c, _ in reach), 0.5, places=2)
            if role == "receiver":
                self.assertAlmostEqual(max(d for _, _, d in reach), prosthesis.RECEIVER_DROP, places=2)
            if role != "donor":
                self.assertEqual([h for h, _, _ in reach], [h for h, _, _ in base])
            if role != "carrier":
                self.assertEqual([c for _, c, _ in reach], [c for _, c, _ in base])
            if role != "receiver":
                self.assertEqual([d for _, _, d in reach], [d for _, _, d in base])
        # Stations not on the path go on as they were.
        for station, kit in self.kits.items():
            if station not in recruits:
                self.assertEqual(self.state(kit, 233.3), (network.base_head_yaw(kit, 233.3), network.base_carriage(kit, 233.3),
                                                          network.base_yoke_drop(kit, 233.3)))

    def test_the_three_parts_are_three_kinds_of_movement(self):
        network, prosthesis, refrain = self.network, self.prosthesis, self.refrain
        for station, (role, when, _) in prosthesis.recruits().items():
            kit = self.kits[station]
            reach = max(prosthesis.donor_reach(kit, when + i / 10.0) for i in range(30))
            # Only a donor's head assembly travels, and the same distance on every donor.
            self.assertAlmostEqual(reach, 1.2 if role == "donor" else 0.0, places=2)
            self.assertEqual(prosthesis.donor_reach(kit, when), 0.0)
            # It stays on its platform, clear of the frame's post and the yoke.
            y = refrain.HEAD_AT[1] + reach
            self.assertLess(abs(y), 4.0 - 0.9)
            self.assertGreater(math.hypot(refrain.HEAD_AT[0], y + 2.6), 2.5)       # the post at (0, -2.6)
            self.assertGreater(math.hypot(refrain.HEAD_AT[0], y), 1.0 + 0.9 + 0.5)  # the yoke's face
        # A receiver's yoke comes further down than any procedure took it, and still leaves a
        # clear gap over the platform.
        self.assertGreater(prosthesis.RECEIVER_DROP, 2.0 * refrain.YOKE_DROP)
        self.assertGreater(refrain.YOKE_HEIGHT - 0.24 - prosthesis.RECEIVER_DROP - 0.25, 1.5)
        # Stations not on the path never do either.
        for station, kit in self.kits.items():
            if station not in prosthesis.recruits():
                self.assertEqual(prosthesis.donor_reach(kit, 230.0), 0.0)
                self.assertLessEqual(refrain.yoke_drop(kit, 233.3), refrain.YOKE_DROP)

    def test_every_carrier_runs_to_the_same_place_and_touches_nothing(self):
        network, prosthesis, refrain = self.network, self.prosthesis, self.refrain
        carriers = {s: e for s, e in prosthesis.recruits().items() if e[0] == "carrier"}
        self.assertEqual(sorted(carriers), [178, 209, 225])
        self.assertEqual({s: e[1] for s, e in carriers.items()}, {225: 220.0, 209: 226.25, 178: 237.5})   # timing as it was
        self.assertEqual(prosthesis.CARRIER_RUN, 2.4)
        stations = self.field.stations()
        for station, (_, when, _) in carriers.items():
            kit = self.kits[station]
            runs = [refrain.carriage(kit, when + i / 30.0) for i in range(0, 75) if when + i / 30.0 <= 240.0]
            # The same endpoint and the same extension for every carrier, however far from the camera.
            if when + 1.4 <= 240.0:
                self.assertAlmostEqual(max(r for r, _ in runs), 2.4, places=3)
                self.assertAlmostEqual(max(e for _, e in runs), 0.5, places=3)
            self.assertAlmostEqual(runs[0][0], 0.8, places=3)               # from where the lane left it
            for run, extend in runs:
                x = refrain.CARRIAGE_HOME + run                              # centre, along the rail, on the unit
                # On its rail, on its unit: the rail is 7 m long and the carriage 0.8 m wide.
                self.assertTrue(-3.1 <= x <= 3.1)
                # Clear of the frame's post (at the unit's centre line, 2.6 m out, 0.12 m thick)...
                self.assertGreater((refrain.RAIL_Y - 0.35) - (2.6 + 0.12), 0.2)
                # ...of the yoke bar, which ends 2.5 m out...
                self.assertGreater((refrain.RAIL_Y - 0.35) - 2.5, 0.4)
                # ...of the platform, and under the beam.
                self.assertGreater(math.hypot(x, refrain.RAIL_Y) - 0.55, 1.3 + 0.5)
                self.assertLess(1.0 + extend, 4.4 - 0.15 - 2.0)
                # And never inside the lane.
                for dx in (-0.4, 0.4):
                    along, across = network.lane_coordinates(kit.x + kit.front * (x + dx), kit.y + refrain.RAIL_Y)
                    self.assertFalse(0.0 <= along <= network.LANE_LENGTH and abs(across) < network.LANE_HALF_WIDTH)
        # A carrier does nothing but run and extend: its head and yoke are as they were.
        for station, (_, when, _) in carriers.items():
            kit = self.kits[station]
            self.assertEqual(refrain.head_yaw(kit, when + 0.7), network.base_head_yaw(kit, when + 0.7))
            self.assertEqual(refrain.yoke_drop(kit, when + 0.7), network.base_yoke_drop(kit, when + 0.7))
            self.assertEqual(prosthesis.donor_reach(kit, when + 0.7), 0.0)

    def test_each_part_is_played_the_moment_its_station_is_recruited(self):
        prosthesis, refrain = self.prosthesis, self.refrain
        order = [station for station, _, _ in prosthesis.PATH]
        # It goes all the way round: its ends are the stations either side of the lane's mouth.
        ends = [self.network.lane_coordinates(self.kits[s].x, self.kits[s].y) for s in (order[0], order[-1])]
        self.assertTrue(all(along < 6.0 for along, _ in ends) and ends[0][1] > 0 > ends[1][1])
        for station, (role, when, _) in prosthesis.recruits().items():
            self.assertIsNone(prosthesis.turn(station, when - 0.01))
            self.assertEqual(prosthesis.turn(station, when), 0.0)
            # No jump as it starts: its first stroke begins from exactly where it was.
            kit = self.kits[station]
            before, after = self.state(kit, when - 1e-4), self.state(kit, when + 1e-4)
            self.assertAlmostEqual(before[0], after[0], delta=0.1)
            self.assertAlmostEqual(before[1][0], after[1][0], places=3)
            self.assertAlmostEqual(before[2], after[2], places=3)
        # A station that joins acts as one with the station it joins: same part, same moment.
        for partner, joins in prosthesis.PARTNERS:
            self.assertEqual(prosthesis.recruits()[partner], prosthesis.recruits()[joins])
            self.assertEqual(prosthesis.turn(partner, 238.0), prosthesis.turn(joins, 238.0))
        self.assertAlmostEqual(prosthesis.turn(237, 211.25), 0.0)

    def test_the_camera_is_looking_when_each_part_is_played(self):
        prosthesis, refrain = self.prosthesis, self.refrain
        from procedural_disagreement.core.vec import q_conj
        focal = 180.0 / math.tan(math.radians(25.0))
        stations = self.field.stations()

        def in_frame(station, t):
            position, rotation, _ = refrain.camera_pose(t)
            v = q_rotate(q_conj(rotation), sub((stations[station].x, stations[station].y, refrain.TOP + 2.0), position))
            return v[2] < 0 and abs(v[0] / -v[2] * focal) < 320.0 and abs(v[1] / -v[2] * focal) < 180.0

        unseen = []
        for station, (_, when, _) in prosthesis.recruits().items():
            if not (in_frame(station, when) and in_frame(station, when + 1.4)):
                unseen.append(station)
        # One station cannot be shown: 176 joins 177, and they are never in the picture together.
        self.assertEqual(unseen, [176])
        # The block is in the picture for the whole of its index.
        for t in (prosthesis.RELAY_BEGINS, prosthesis.RELAY_BEGINS + 0.6):
            position, rotation, _ = refrain.camera_pose(t)
            v = q_rotate(q_conj(rotation), sub((stations[224].x, stations[224].y, refrain.TOP), position))
            self.assertTrue(v[2] < 0 and abs(v[0] / -v[2] * focal) < 320.0 and abs(v[1] / -v[2] * focal) < 180.0)
        # The gaze never whips: under 30 degrees a second.
        previous = q_rotate(refrain.camera_pose(210.0)[1], (0.0, 0.0, -1.0))
        for i in range(1, 901):
            forward = q_rotate(refrain.camera_pose(210.0 + i / 30.0)[1], (0.0, 0.0, -1.0))
            self.assertLess(math.degrees(math.acos(max(-1.0, min(1.0, dot(previous, forward))))), 1.0)
            previous = forward
        # It turns the other way round from the path and meets the direction of travel again at 4:00.
        def yaw(t):
            f = q_rotate(refrain.camera_pose(t)[1], (0.0, 0.0, -1.0))
            return math.degrees(math.atan2(f[0], f[1])) % 360.0
        self.assertAlmostEqual(yaw(240.0), 304.0, places=3)
        self.assertTrue(yaw(220.0) < 15.0 or yaw(220.0) > 345.0)          # looking north, across the lane's end

    def test_the_absence_stays(self):
        network, prosthesis, refrain = self.network, self.prosthesis, self.refrain
        lane = [piece for piece in self.hinge.pieces() if network._across_lane(piece)]
        self.assertEqual(len(lane), 21)
        for t in (211.0, 220.0, 230.0, 240.0):
            for piece in lane:
                self.assertEqual(prosthesis.piece_offset(piece, t), (0.0, 0.0, 0.0))
                self.assertLess(network.piece_offset(piece, t)[2], -piece.size[2])     # still below the ground
            # Nothing that moves comes inside the lane's width.
            for piece in self.hinge.pieces():
                if not prosthesis.moves(piece):
                    continue
                dx, dy, dz = prosthesis.piece_offset(piece, t)
                for i in (-0.5, 0.0, 0.5):
                    for j in (-0.5, 0.0, 0.5):
                        along, across = network.lane_coordinates(piece.center[0] + dx + piece.size[0] * i,
                                                                 piece.center[1] + dy + piece.size[1] * j)
                        self.assertFalse(0.0 <= along <= network.LANE_LENGTH and abs(across) < network.LANE_HALF_WIDTH)
            # What the lane left held is still held: the frames, and the stations facing it.
            for station in network.flanking():
                self.assertAlmostEqual(network.gantry_yaw(self.kits[station], t), -12.0, delta=0.01)
            for kit in self.kits.values():
                if network.beside_lane(kit):
                    self.assertEqual(network.held(kit, t), 1.0)
        # The path does not recruit a single station inside the lane, because none stands there.
        for station in prosthesis.recruits():
            kit = self.kits[station]
            for i in (-4.0, 0.0, 4.0):
                for j in (-4.0, 0.0, 4.0):
                    along, across = network.lane_coordinates(kit.x + i, kit.y + j)
                    self.assertFalse(0.0 <= along <= network.LANE_LENGTH and abs(across) < network.LANE_HALF_WIDTH)

    def test_the_camera_leaves_the_lane_and_goes_round_with_the_path(self):
        network, prosthesis, refrain = self.network, self.prosthesis, self.refrain
        previous = refrain.camera_position(210.0)
        for i in range(1, 901):
            position = refrain.camera_position(210.0 + i / 30.0)
            self.assertLess(length(sub(position, previous)), 0.21)                 # never above 6.3 m/s
            self.assertTrue(5.9 < position[2] - self.hinge.GROUND < 12.6)          # close, never a flyover
            previous = position
        # Between the two stations that close the lane, then round the block to the right.
        between = refrain.camera_position(215.5)
        s = self.field.stations()
        self.assertTrue(s[224].x + 4.0 < between[0] < s[237].x - 4.0)
        headings = []
        for t in (210.5, 215.0, 220.0, 225.0, 232.0, 239.5):
            a, b = refrain.camera_position(t), refrain.camera_position(t + 0.1)
            headings.append(math.degrees(math.atan2(b[0] - a[0], b[1] - a[1])) % 360.0)
        self.assertEqual(headings, sorted(headings))                               # it only ever turns right
        self.assertGreater(headings[-1] - headings[0], 150.0)                      # most of the way round
        # It ends on the south bank, off the lane's axis, still moving.
        end = refrain.camera_position(240.0)
        self.assertLess(network.lane_coordinates(end[0], end[1])[1], -20.0)
        self.assertGreater(length(sub(end, refrain.camera_position(239.9))), 0.25)
        for i in range(0, 901, 5):
            position = refrain.camera_position(210.0 + i / 30.0)
            for kit in self.kits.values():
                gap = (max(0.0, abs(position[0] - kit.x) - 4.0), max(0.0, abs(position[1] - kit.y) - 4.0),
                       max(0.0, position[2] - (refrain.TOP + 4.6)))
                self.assertGreater(math.hypot(*gap), 3.0)


class ClimaxTests(unittest.TestCase):
    """4:00-4:15: the compensation becomes the network."""

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.core import climax, hinge, landfill, network, prosthesis, refrain
        cls.climax, cls.hinge, cls.field, cls.network, cls.prosthesis, cls.refrain = climax, hinge, landfill, network, prosthesis, refrain
        cls.kits = {kit.station: kit for kit in refrain.kits() + refrain.later_kits()}
        cls.moving = [piece for piece in hinge.pieces() if climax.moves(piece)]

    def state(self, kit, t):
        r = self.refrain
        return r.head_yaw(kit, t), r.carriage(kit, t), r.yoke_drop(kit, t), self.climax.donor_reach(kit, t)

    def angles(self, t):
        f = q_rotate(self.refrain.camera_pose(t)[1], (0.0, 0.0, -1.0))
        return math.degrees(math.atan2(f[0], f[1])), -math.degrees(math.asin(f[2]))

    def test_it_starts_from_exactly_the_locked_state(self):
        climax, prosthesis, refrain = self.climax, self.prosthesis, self.refrain
        self.assertEqual(climax.START, 240.0)
        self.assertEqual(refrain.camera_pose(240.0), prosthesis.camera_pose(240.0))
        self.assertEqual(refrain.sight(240.0), 135.0)
        for kit in self.kits.values():
            locked = (prosthesis.head_yaw(kit, 240.0), prosthesis.carriage(kit, 240.0), prosthesis.yoke_drop(kit, 240.0),
                      prosthesis.donor_reach(kit, 240.0))
            self.assertEqual(self.state(kit, 240.0), locked)
            # And it goes on from there without a step: every stroke under way finishes as it was going to.
            after = self.state(kit, 240.0 + 1e-4)
            self.assertAlmostEqual(after[0], locked[0], delta=0.03)     # a head turns at up to 116 degrees a second
            self.assertAlmostEqual(after[1][0], locked[1][0], places=3)
            self.assertAlmostEqual(after[1][1], locked[1][1], places=3)
            self.assertAlmostEqual(after[2], locked[2], places=3)
            self.assertAlmostEqual(after[3], locked[3], places=3)
        for station in prosthesis.recruits():
            # Until the slip begins, a route station's clock is the route's clock.
            for t in (240.0, 241.0, 243.0, 243.75):
                self.assertAlmostEqual(climax.turn(station, t), prosthesis.turn(station, t), places=9)
        for piece in self.hinge.pieces():
            self.assertEqual(climax.piece_offset(piece, 240.0), (0.0, 0.0, 0.0))
            self.assertLess(max(abs(v) for v in climax.piece_offset(piece, 240.0 + 1e-3)), 1e-6)
        # The camera leaves as it arrives: same place, same velocity, same turning.
        e = 1e-3
        before, at, after = (refrain.camera_position(t) for t in (240.0 - e, 240.0, 240.0 + e))
        for a, b, c in zip(before, at, after):
            self.assertAlmostEqual((b - a) / e, (c - b) / e, places=2)
        a0, a1, a2 = self.angles(240.0 - e), self.angles(240.0), self.angles(240.0 + e)
        for k in (0, 1):
            self.assertAlmostEqual((a1[k] - a0[k]) / e, (a2[k] - a1[k]) / e, places=2)

    def test_nothing_before_four_minutes_changes_and_nothing_from_the_ending(self):
        climax, prosthesis, network = self.climax, self.prosthesis, self.network
        for t in (150.0, 185.0, 205.0, 215.0, 230.0, 239.99, 240.0, 265.0, 270.0, 280.0):
            self.assertFalse(climax.active(t))
            self.assertEqual(climax.sight_more(t), 0.0)
            self.assertEqual(climax.camera_pose(t), prosthesis.camera_pose(t))
            for kit in self.kits.values():
                self.assertEqual(climax.head_yaw(kit, t), prosthesis.head_yaw(kit, t))
                self.assertEqual(climax.carriage(kit, t), prosthesis.carriage(kit, t))
                self.assertEqual(climax.yoke_drop(kit, t), prosthesis.yoke_drop(kit, t))
                self.assertEqual(climax.donor_reach(kit, t), prosthesis.donor_reach(kit, t))
            for piece in self.moving:
                self.assertEqual(climax.piece_offset(piece, t), (0.0, 0.0, 0.0))
        # What the network and the route did to the level is as it was.
        for piece in self.hinge.pieces():
            self.assertEqual(network.piece_offset(piece, 250.0), network.piece_offset(piece, 240.0))
            self.assertEqual(prosthesis.piece_offset(piece, 250.0), prosthesis.piece_offset(piece, 240.0))

    def test_the_lane_stays_empty(self):
        climax, network = self.climax, self.network
        lane = [piece for piece in self.hinge.pieces() if network.intrusion(piece) is not None]
        self.assertEqual(len(lane), 21)
        for piece in lane:
            self.assertIsNone(climax.part(piece))
            for t in (240.0, 245.0, 250.0, 254.375, 255.0):
                self.assertLess(network.piece_offset(piece, t)[2], -piece.size[2])         # still below the ground
        times = [240.0 + i * 0.25 for i in range(61)]
        nearest = {}
        for piece in self.moving:
            kind = climax.part(piece)[0]
            for t in times:
                dx, dy, dz = climax.piece_offset(piece, t)
                if kind in ("bus", "run"):
                    self.assertEqual((dx, dy), (0.0, 0.0))        # they only rise: they cannot come nearer
                gap = climax.lane_clearance((piece.center[0] + dx, piece.center[1] + dy), piece.size)
                nearest[kind] = min(nearest.get(kind, 1e9), gap)
                # Nothing bridges it: no moving piece has parts on both sides of it.
                sides = set()
                for i in (-0.5, -0.25, 0.0, 0.25, 0.5):
                    for j in (-0.5, -0.25, 0.0, 0.25, 0.5):
                        along, across = network.lane_coordinates(piece.center[0] + dx + piece.size[0] * i,
                                                                 piece.center[1] + dy + piece.size[1] * j)
                        if 0.0 <= along <= network.LANE_LENGTH:
                            sides.add(across > 0.0)
                self.assertLess(len(sides), 2)
        self.assertGreater(min(nearest.values()), 0.0)
        # Whatever moves sideways keeps its distance.
        for kind in ("line", "cell"):
            self.assertGreaterEqual(nearest[kind], climax.LANE_MARGIN)
        self.assertGreater(nearest["relay"], 2.0 * climax.LANE_MARGIN)
        # No station's moving part comes inside it, at any frame.
        for kit in self.kits.values():
            hx, hy = kit.x + kit.front * self.refrain.HEAD_AT[0], kit.y + self.refrain.HEAD_AT[1]
            for i in range(0, 451):
                t = 240.0 + i / 30.0
                x, y, _ = network.carriage_position(kit, t)
                points = [(x - 0.4, y), (x + 0.4, y), (hx, hy + climax.donor_reach(kit, t))]
                for px, py in points:
                    along, across = network.lane_coordinates(px, py)
                    self.assertFalse(0.0 <= along <= network.LANE_LENGTH and abs(across) < network.LANE_HALF_WIDTH + 0.5)
        # What the lane left held is still held.
        for t in (245.0, 255.0):
            for station in network.flanking():
                self.assertAlmostEqual(network.gantry_yaw(self.kits[station], t), -12.0, delta=0.01)
            for kit in self.kits.values():
                if network.beside_lane(kit):
                    self.assertEqual(network.held(kit, t), 1.0)

    def test_the_populations_are_deterministic(self):
        climax, prosthesis = self.climax, self.prosthesis
        recruits = climax.recruits()
        self.assertEqual(set(recruits), set(self.kits))                    # every station that has machinery
        for station, (role, when, _) in prosthesis.recruits().items():
            self.assertEqual(recruits[station], (role, when))              # the route is as it was
        count = lambda t: sum(1 for _, when in recruits.values() if when <= t)
        self.assertEqual([count(t) for t in (240.0, 242.5, 245.0, 247.5, 250.0)], [12, 17, 27, 38, 40])
        roles = [role for role, _ in recruits.values()]
        self.assertEqual((roles.count("donor"), roles.count("carrier"), roles.count("receiver")), (17, 12, 11))
        new = sorted((climax.distance(station), when) for station, (_, when) in recruits.items()
                     if station not in prosthesis.recruits())
        # It spreads outward from the lane: nearer first, on the beat, and after 4:00.
        self.assertEqual([when for _, when in new], sorted(when for _, when in new))
        for _, when in new:
            self.assertGreater(when, 240.0)
            self.assertAlmostEqual((when - 240.0) / timeline.BEAT, round((when - 240.0) / timeline.BEAT), places=9)
        # Plain blocks take part now and then: none has machinery, and none is the route's block.
        relays = climax.relays()
        self.assertEqual(len(relays), 21)
        self.assertFalse(set(relays) & set(self.kits))
        self.assertNotIn(prosthesis.RELAY_STATION, relays)
        self.assertLess(len(relays), len(self.field.stations()) // 8)
        # Worked out again from nothing, it is all the same.
        before = (dict(recruits), dict(relays), [climax.part(piece) for piece in self.hinge.pieces()])
        for cached in (climax.recruits, climax.relays, climax.part, climax.distance, climax._slip, climax.hands_to):
            cached.cache_clear()
        self.assertEqual(before, (climax.recruits(), climax.relays(), [climax.part(piece) for piece in self.hinge.pieces()]))

    def test_a_new_station_takes_its_part_from_where_it_was(self):
        climax = self.climax
        for station, (role, when) in climax.recruits().items():
            self.assertIsNone(climax.turn(station, when - 0.01))
            if station in self.prosthesis.recruits():
                continue
            self.assertEqual(climax.turn(station, when), 0.0)
            kit = self.kits[station]
            before, after = self.state(kit, when - 1e-4), self.state(kit, when + 1e-4)
            self.assertAlmostEqual(before[0], after[0], delta=0.05)
            self.assertAlmostEqual(before[1][0], after[1][0], places=3)
            self.assertAlmostEqual(before[2], after[2], places=3)
            self.assertAlmostEqual(before[3], after[3], places=3)
            # A donor hands on to a station that is not itself.
            if role == "donor":
                self.assertIn(climax.hands_to(station), self.kits)
                self.assertNotEqual(climax.hands_to(station), station)

    def test_everything_comes_onto_one_clock(self):
        climax, period = self.climax, self.refrain.PERIOD
        # From saturation a station's place in its turn depends only on how far it is from the lane.
        for t in (251.25, 253.0, 255.0):
            for station in climax.recruits():
                expected = (t - climax.reached(climax.distance(station))) % period
                difference = (climax.turn(station, t) - expected + period * 0.5) % period - period * 0.5
                self.assertAlmostEqual(difference, 0.0, places=6)
        for partner, joins in self.prosthesis.PARTNERS:
            for t in (242.0, 248.0, 254.0):
                self.assertAlmostEqual(climax.turn(partner, t), climax.turn(joins, t), places=9)
        # Getting there, no station ever runs backward.
        for station in self.prosthesis.recruits():
            previous = climax.turn(station, 240.0)
            for i in range(1, 451):
                now = climax.turn(station, 240.0 + i / 30.0)
                step = (now - previous + period * 0.5) % period - period * 0.5
                self.assertGreater(step, 0.0)
                self.assertLess(step, 2.0 / 30.0)                          # nor faster than twice its speed
                previous = now
        # Relays run on the same clock.
        for station, (when, sign) in climax.relays().items():
            place = self.field.stations()[station]
            self.assertEqual(when, climax.reached(self.network.lane_distance(place.x, place.y)))
            self.assertIn(sign, (1, -1))

    def test_the_large_structures_are_bounded_and_slow(self):
        climax = self.climax
        limits = {"relay": (0.0, climax.RELAY_INDEX, 0.0), "line": (climax.LINE_SHIFT, climax.LINE_SHIFT, 0.0),
                  "cell": (0.0, climax.CELL_SHEAR, 0.0), "bus": (0.0, 0.0, sum(climax.BUS_RISE)), "run": (0.0, 0.0, climax.RUN_RISE)}
        kinds = {}
        for piece in self.moving:
            kind = climax.part(piece)[0]
            kinds[kind] = kinds.get(kind, 0) + 1
            previous = climax.piece_offset(piece, 240.0)
            for i in range(1, 451):
                offset = climax.piece_offset(piece, 240.0 + i / 30.0)
                for value, limit in zip(offset, limits[kind]):
                    self.assertLessEqual(abs(value), limit + 1e-9)
                self.assertGreaterEqual(offset[2], 0.0)                    # nothing here goes down
                speed = max(abs(a - b) for a, b in zip(offset, previous)) * 30.0
                self.assertLess(speed, 3.0)                                # metres a second
                previous = offset
            if kind != "relay":
                # Every large stroke has arrived by the peak, and stays.
                self.assertEqual(climax.piece_offset(piece, climax.PEAK), climax.piece_offset(piece, climax.END))
                self.assertEqual(climax.piece_offset(piece, climax.END), climax.piece_offset(piece, 262.0))
        self.assertEqual(kinds, {"relay": 42, "line": 172, "cell": 85, "bus": 19, "run": 138})
        # At the peak: the buses up, the runs up, the cells and the lines across.
        at_peak = {}
        for piece in self.moving:
            kind = climax.part(piece)[0]
            if kind != "relay":
                at_peak.setdefault(kind, set()).add(round(max(abs(v) for v in climax.piece_offset(piece, climax.PEAK)), 6))
        self.assertEqual(at_peak, {"line": {1.0}, "cell": {2.0}, "bus": {3.0}, "run": {1.6}})

    def test_a_cut_trunk_or_main_answers_on_both_sides_at_once(self):
        climax, network = self.climax, self.network
        cuts = climax._cuts()
        self.assertEqual(len(cuts), 3)                                     # two trunks and the heavy main
        paired = 0
        for line, places in cuts.items():
            runs = [piece for piece in self.hinge.pieces() if piece.kind in ("trunk", "main")
                    and climax._line(piece) == line and network.intrusion(piece) is None]
            below = [r for r in runs if climax._index(r) == min(places) - 1]
            above = [r for r in runs if climax._index(r) == max(places) + 1]
            self.assertEqual((len(below), len(above)), (1, 1))
            a, b = climax.part(below[0]), climax.part(above[0])
            if a is None or b is None:
                # One side passes through a station and stays down (below): no pair to compare.
                self.assertTrue(climax._under_a_platform(below[0]) or climax._under_a_platform(above[0]))
                continue
            self.assertEqual(a, b)                                         # same movement, same moment
            for t in (247.5, 250.0, 252.5, 254.0):
                self.assertEqual(climax.piece_offset(below[0], t), climax.piece_offset(above[0], t))
            paired += 1
        self.assertEqual(paired, 2)                                        # the heavy main, and one trunk

    def test_nothing_rises_into_a_station(self):
        climax = self.climax
        # A run that passes through a station with machinery stays down: risen, it would stand
        # in the place that station keeps empty.
        for piece in self.moving:
            if climax.part(piece)[0] not in ("bus", "run") or piece.kind == "via":
                continue
            for kit in self.kits.values():
                self.assertFalse(abs(piece.center[0] - kit.x) < piece.size[0] * 0.5 + 4.0
                                 and abs(piece.center[1] - kit.y) < piece.size[1] * 0.5 + 4.0)
        # And nothing that moves sideways moves into one.
        for piece in self.moving:
            if climax.part(piece)[0] != "cell":
                continue
            for way in (-climax.CELL_SHEAR, climax.CELL_SHEAR):
                for kit in self.kits.values():
                    self.assertFalse(abs(piece.center[0] - kit.x) < piece.size[0] * 0.5 + 4.0
                                     and abs(piece.center[1] + way - kit.y) < piece.size[1] * 0.5 + 4.0)

    def test_the_camera_climbs_away_and_never_cuts(self):
        climax, refrain = self.climax, self.refrain
        previous, gaze = refrain.camera_position(240.0), q_rotate(refrain.camera_pose(240.0)[1], (0.0, 0.0, -1.0))
        travelled = 0.0
        for i in range(1, 451):
            t = 240.0 + i / 30.0
            position, rotation, fov = refrain.camera_pose(t)
            step = length(sub(position, previous))
            travelled += step
            self.assertLess(step, 0.19)                                    # never above 5.7 m/s
            self.assertGreaterEqual(position[2], previous[2] - 1e-9)       # it only climbs
            forward = q_rotate(rotation, (0.0, 0.0, -1.0))
            self.assertLess(math.degrees(math.acos(max(-1.0, min(1.0, dot(gaze, forward))))), 0.6)    # under 18 deg/s
            self.assertEqual(fov, refrain.camera_pose(240.0)[2])
            for kit in self.kits.values():
                gap = (max(0.0, abs(position[0] - kit.x) - 4.0), max(0.0, abs(position[1] - kit.y) - 4.0),
                       max(0.0, position[2] - (refrain.TOP + 4.6)))
                self.assertGreater(math.hypot(*gap), 4.0)
            previous, gaze = position, forward
        self.assertTrue(60.0 < travelled < 70.0)
        # It only ever turns right, as it was turning at 4:00, and looks further down as it climbs.
        yaws = [(self.angles(240.0 + i * 0.5)[0] + 56.0) % 360.0 for i in range(1, 31)]
        self.assertEqual(yaws, sorted(yaws))
        pitches = [self.angles(240.0 + i * 0.5)[1] for i in range(31)]
        self.assertEqual(pitches, sorted(pitches))
        self.assertTrue(refrain.sight(245.0) < refrain.sight(250.0) <= refrain.sight(255.0) == 240.0)
        # It does its turning early: most of the way round before the structure joins, and all
        # but still through saturation.
        turned = lambda t: (self.angles(t)[0] + 56.0) % 360.0
        self.assertGreater(turned(246.25), 0.5 * turned(255.0))
        self.assertGreater(turned(250.0), 0.9 * turned(255.0))
        for i in range(0, 94):
            t = 251.25 + i / 30.0
            self.assertLess((turned(t + 1.0 / 30.0) - turned(t)) * 30.0, 2.0)          # degrees a second
        # And it is settling before the structure has gone far: under 4 degrees a second from 4:08.5.
        for i in range(0, 83):
            t = 248.5 + i / 30.0
            self.assertLess((turned(t + 1.0 / 30.0) - turned(t)) * 30.0, 4.0)
        # Its turning has no corners: neither its speed nor its acceleration steps.
        rates = [((self.angles(240.0 + (i + 1) / 240.0)[0] - self.angles(240.0 + i / 240.0)[0] + 180.0) % 360.0 - 180.0) * 240.0
                 for i in range(3600)]
        accelerations = [(b - a) * 240.0 for a, b in zip(rates, rates[1:])]
        self.assertLess(max(rates), 17.5)
        self.assertGreater(min(rates), 0.0)
        self.assertLess(max(abs(b - a) for a, b in zip(accelerations, accelerations[1:])), 0.1)
        self.assertTrue(3.9 < rates.index(max(rates)) / 240.0 < 5.0)       # fastest at about 4:04

    def test_the_state_before_four_fifteen_is_fixed(self):
        climax, network, refrain = self.climax, self.network, self.refrain
        position, rotation, _ = refrain.camera_pose(255.0)
        for value, expected in zip(position, (98.9, 105.6, 49.75)):
            self.assertAlmostEqual(value, expected, places=6)
        yaw, pitch = self.angles(255.0)
        self.assertAlmostEqual(pitch, 32.0, places=6)
        # It is looking at the middle of the lane, with the whole length of it in the picture.
        from procedural_disagreement.core.vec import q_conj
        focal = 180.0 / math.tan(math.radians(25.0))
        for along, limit in ((30.0, 2.0), (0.0, 320.0), (60.0, 320.0)):
            x, y = network.lane_point(along)
            v = q_rotate(q_conj(rotation), sub((x, y, self.hinge.GROUND), position))
            self.assertLess(v[2], 0.0)
            self.assertLess(abs(v[0] / -v[2] * focal), limit)
            self.assertLess(abs(v[1] / -v[2] * focal), 20.0)
        # It is still moving, and it holds there until what follows is made.
        self.assertGreater(length(sub(position, refrain.camera_position(254.9))), 0.3)
        self.assertEqual(refrain.camera_pose(260.0), refrain.camera_pose(255.0))


class CodaTests(unittest.TestCase):
    """4:15-4:25: the room, with nobody in it, and what it keeps of them."""

    FRAMES = [n / 30.0 for n in range(7651, 7950)]

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.core import coda
        cls.coda = coda
        cls.marks = coda.marks()
        cls.p = variants.primary()

    def room(self, t):
        """Everything the ending's first frame depends on."""
        v = self.p
        return (ch.camera_pose(t), ch.which_camera(t), ch.camera_is_below(t), outer.subject_presence(t),
                outer.alternates_presence(t), outer.coupling(t), outer.clock(t), outer.lamp_height(t), outer.room_light(t),
                outer.zone_levels(t), outer.conduit_open(t), outer.opening_panel(t), ch.reindex_carriage(t),
                ch.reindex_head(v, t, v.tower_fail_time), ch.receiver_offset(t), ch.rotor_angle(v, t, ch.NEVER))

    def test_nothing_at_or_before_four_fifteen_changes(self):
        coda = self.coda
        for t in (200.0, 240.0, 254.9667, 255.0):
            self.assertFalse(outer.in_coda(t))
            self.assertFalse(outer.after_the_case(t))
            self.assertEqual((outer.coupling(t), outer.clock(t), outer.room_light(t)), (1.0, t, 1.0))
            self.assertEqual((outer.subject_presence(t), outer.alternates_presence(t), outer.lamp_height(t)), (1.0, 1.0, 0.0))
            self.assertEqual(ch.camera_pose(t), ch._film_camera(t))
            self.assertEqual(ch.which_camera(t), "hinge")
            self.assertTrue(ch.camera_is_below(t))
            for mark in self.marks:
                self.assertEqual(coda.level(mark, t), 0.0)
                self.assertEqual(coda.pose(mark, t)[1], (0.0, 0.0, 0.0))

    def test_the_first_new_frame_is_the_room_from_the_outer_frame(self):
        first = 7651 / 30.0
        self.assertEqual(ch.which_camera(first), "upper")
        self.assertFalse(ch.camera_is_below(first))
        # One cut, straight after 4:15.0; then the same still frame all the way into the ending.
        for t in self.FRAMES + [265.0, 270.0, 279.9]:
            self.assertEqual(ch.which_camera(t), "upper")
            self.assertEqual(ch.camera_pose(t), ch._outer_camera())

    def test_nobody_is_there(self):
        for t in self.FRAMES:
            self.assertEqual(outer.subject_presence(t), 0.0)
            self.assertEqual(outer.alternates_presence(t), 0.0)
            self.assertEqual(ch.presence(variants.alternate(), t), 0.0)

    def test_no_mark_is_writing(self):
        coda = self.coda
        self.assertEqual({mark.kind for mark in self.marks}, {"scrawl", "bar"})
        # A scrawl is short straight pieces; a bar is one plain upright rectangle.
        for mark in self.marks:
            if mark.kind == "scrawl":
                self.assertLess(mark.size[0], 0.9)
            else:
                self.assertEqual(mark.rotation, (1.0, 0.0, 0.0, 0.0))
        # A trace never closes on itself or crosses itself: no loops, no boxes, no characters.
        for seed in range(40):
            points = coda._trace(9000 + seed * 13, (0.0, 0.0), 0.0, 20, 0.4, (-0.2, 7.0, -0.9, 0.9), clear=0.45, base=0.0)
            for i, a in enumerate(points):
                for b in points[i + 2:]:
                    self.assertGreater(math.hypot(a[0] - b[0], a[1] - b[1]), 0.45)
        # On the wall a trace runs on across panels: metres long, not the size of a character.
        for group in range(len(coda.SCRAWLED_RUNS)):
            xs = [mark.center[0] for mark in self.marks if mark.kind == "scrawl" and mark.group == group]
            zs = [mark.center[2] for mark in self.marks if mark.kind == "scrawl" and mark.group == group]
            self.assertGreater(max(max(xs) - min(xs), max(zs) - min(zs)), 3.0)
        # Bars are ranked: in every group each row is shorter than the one above, squared at one end.
        for group in range(len(coda.BARRED_PANELS)):
            rows = {}
            for mark in self.marks:
                if mark.kind == "bar" and mark.group == group:
                    rows.setdefault(round(mark.center[2], 3), []).append(mark.center[0])
            counts = [len(rows[z]) for z in sorted(rows, reverse=True)]
            self.assertEqual(counts, sorted(counts, reverse=True))
            self.assertEqual(len(set(counts)), len(counts))
            self.assertEqual(len({round(min(xs), 6) for xs in rows.values()}), 1)

    def test_the_first_statement_sets_both_conditions_out(self):
        coda = self.coda
        scrawl = [coda.extent("scrawl", t) for t in self.FRAMES]
        bar = [coda.extent("bar", t) for t in self.FRAMES]
        # Scrawls: faintly there from the first frame, all there by the word, and nothing added after.
        self.assertGreater(scrawl[0], 0.5 * max(scrawl))
        self.assertAlmostEqual(coda.extent("scrawl", coda.SCRAWLS), max(scrawl), places=6)
        self.assertAlmostEqual(coda.extent("scrawl", coda.AGAIN), max(scrawl), places=6)
        # Bars: none until the second line; all there by the word; nothing added after.
        self.assertEqual(coda.extent("bar", coda.ORDER), 0.0)
        self.assertAlmostEqual(coda.extent("bar", coda.BARS), max(bar), places=6)
        self.assertAlmostEqual(coda.extent("bar", coda.WITHDRAW), max(bar), places=6)
        # Both maxima fall inside the first statement, and both stand together until the second.
        self.assertTrue(coda.SCRAWLS < coda.BARS < coda.AGAIN)
        self.assertGreater(max(scrawl), 30.0)
        self.assertGreater(max(bar), 10.0)
        # The bars do not come out of the scrawls: no scrawl changes while the bars arrive.
        self.assertEqual(coda.extent("scrawl", coda.ORDER), coda.extent("scrawl", coda.BARS))

    def test_the_second_statement_withdraws_them_and_the_bars_go_last(self):
        coda = self.coda
        previous = None
        for t in self.FRAMES:
            now = (coda.extent("scrawl", t), coda.extent("bar", t))
            if t > coda.AGAIN and previous is not None:
                self.assertLessEqual(now[0], previous[0] + 1e-9)       # nothing comes back
                self.assertLessEqual(now[1], previous[1] + 1e-9)
            # While any scrawl is left, every bar is still there.
            if t > coda.BARS and now[0] > 0.0:
                self.assertAlmostEqual(now[1], coda.extent("bar", coda.BARS), places=6)
            previous = now
        # The scrawls stay whole through the second statement until the word that names them,
        # and go inside it: "scrawls" is sung from 4:21.65 to 4:22.10.
        whole = coda.extent("scrawl", coda.AGAIN)
        self.assertGreaterEqual(coda.extent("scrawl", 261.5), 0.9 * whole)
        self.assertEqual(coda.extent("scrawl", 261.5), whole)
        self.assertLess(coda.extent("scrawl", 261.7), whole)                           # it has begun
        self.assertGreater(coda.extent("scrawl", 261.65), 0.9 * whole)
        self.assertLess(coda.extent("scrawl", 262.1), 0.05 * whole)                    # nearly all of it, in the word
        self.assertEqual(coda.extent("scrawl", 262.2), 0.0)
        # Then the bars are alone, all of them, until their own withdrawal begins.
        self.assertEqual(coda.extent("bar", 262.2), coda.extent("bar", coda.BARS))
        self.assertEqual(coda.extent("bar", coda.WITHDRAW), coda.extent("bar", coda.BARS))
        self.assertLess(coda.extent("bar", coda.WITHDRAW + 0.3), coda.extent("bar", coda.BARS))
        bars = [mark for mark in self.marks if mark.kind == "bar"]
        self.assertAlmostEqual(min(mark.leaves[0] for mark in bars), 262.5, places=6)
        self.assertAlmostEqual(max(mark.leaves[0] + mark.leaves[1] for mark in bars), 264.6, places=6)
        self.assertAlmostEqual(max(mark.arrives[0] + mark.arrives[1] for mark in bars), 259.09, places=2)
        # The bars go group by group; in the last word only the last group is left, and that is
        # the one the outer frame sees behind the place the chest was.
        self.assertEqual(coda.groups_present("bar", coda.WITHDRAW), [0, 1, 2])
        self.assertEqual(coda.groups_present("bar", coda.LAST), [2])
        self.assertGreater(coda.extent("bar", coda.LAST + 0.2), 0.0)
        self.assertEqual(coda.extent("bar", coda.SILENT), 0.0)
        position, _, _ = ch.camera_pose(260.0)
        chest = (0.0, 0.0, 3.0)
        x, y, z = coda._panel_face(*coda.BARRED_PANELS[-1])
        k = (y - position[1]) / (chest[1] - position[1])
        self.assertLess(abs(position[0] + (chest[0] - position[0]) * k - x), 1.0)
        self.assertLess(abs(position[2] + (chest[2] - position[2]) * k - z), 1.0)

    def test_nothing_explicit_reaches_the_ending(self):
        coda = self.coda
        for t in (264.6, 264.8, 7949 / 30.0, 265.0, 265.0333, 270.0, 280.0):
            for mark in self.marks:
                self.assertEqual(coda.level(mark, t), 0.0)
                self.assertEqual(coda.pose(mark, t)[1], (0.0, 0.0, 0.0))

    def test_the_system_winds_down_to_exactly_the_endings_first_state(self):
        # Three things change, and each only goes one way: circulation dies, the lamp lets go,
        # the room goes down.
        previous = self.room(self.FRAMES[0])
        for t in self.FRAMES[1:]:
            now = self.room(t)
            self.assertLessEqual(now[5], previous[5])                  # coupling
            self.assertGreaterEqual(now[6], previous[6])               # the clock never runs back
            self.assertGreaterEqual(now[7], previous[7])               # the lamp only rises
            self.assertLessEqual(now[8], previous[8] + 1e-12)          # light
            # Nothing else in the room moves at all.
            self.assertEqual((now[0], now[10], now[11], now[14]), (previous[0], previous[10], previous[11], previous[14]))
            for a, b in zip(now[12], previous[12]):
                self.assertAlmostEqual(a, b, places=12)
            self.assertEqual(now[13], previous[13])
            previous = now
        self.assertEqual(outer.coupling(self.FRAMES[0]), 0.5)
        self.assertEqual(outer.lamp_height(262.5), 0.0)
        self.assertEqual(outer.zone_levels(260.0), (0.0,) * 7)
        # By the end of the last sung word it is all exactly as the ending finds it.
        ending = self.room(265.0)
        for t in (264.6, 264.8, 7949 / 30.0):
            now = self.room(t)
            for index, (a, b) in enumerate(zip(now, ending)):
                if index == 12:
                    for x, y in zip(a, b):
                        self.assertAlmostEqual(x, y, places=12)
                else:
                    self.assertEqual(a, b, index)
        self.assertEqual((ending[5], ending[6], ending[7], ending[8]), (0.0, 265.0, 0.2, 0.26))

    def test_nothing_after_four_twenty_five_changes(self):
        for t in (265.0, 267.006, 270.71, 275.714, 279.9667):
            self.assertFalse(outer.in_coda(t))
            self.assertTrue(outer.in_ending(t))
            self.assertEqual((outer.coupling(t), outer.clock(t), outer.subject_presence(t)), (0.0, 265.0, 0.0))
        self.assertEqual(outer.lamp_height(265.0), outer.LAMP_RAISED_ENDING)
        self.assertEqual(outer.room_light(265.0), 0.26)
        # The ending's first action is still the tower head's, at 4:27.006: nothing anticipates it.
        self.assertEqual(outer.ending_head(267.0), 0.0)
        self.assertGreater(outer.ending_head(267.2), 0.0)


class LookTests(unittest.TestCase):
    """The look is presentation only: it may not reach anything the film authored."""

    def test_the_lookdev_profile_builds_the_previews_own_scene(self):
        import dataclasses
        preview, lookdev = dataclasses.asdict(profiles.PREVIEW), dataclasses.asdict(profiles.LOOKDEV)
        # Everything that decides which objects exist and where is the preview's.
        for field in ("cylinder_segments", "sphere_segments", "slice_subdivisions", "conduit_pitch", "bevel_width",
                      "wall_pipes", "extra_alternates"):
            self.assertEqual(preview[field], lookdev[field], field)
        self.assertEqual(variants.for_profile(profiles.PREVIEW), variants.for_profile(profiles.LOOKDEV))
        self.assertTrue(profiles.LOOKDEV.look)
        self.assertFalse(profiles.PREVIEW.look)
        self.assertTrue(profiles.FINAL.look)

    def test_the_final_profile_renders_the_approved_scene_only_at_higher_quality(self):
        import dataclasses
        lookdev, final = dataclasses.asdict(profiles.LOOKDEV), dataclasses.asdict(profiles.FINAL)
        # Everything but the name, the resolution and the samples is lookdev's (director,
        # 2026-10-22: quality only).
        for field in lookdev:
            if field not in ("name", "width", "height", "samples"):
                self.assertEqual(lookdev[field], final[field], field)
        self.assertEqual((final["width"], final["height"]), (3840, 2160))
        self.assertEqual(variants.for_profile(profiles.FINAL), variants.for_profile(profiles.LOOKDEV))

    def test_no_core_module_knows_about_the_look(self):
        core = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "procedural_disagreement", "core")
        for name in sorted(os.listdir(core)):
            if not name.endswith(".py") or name in ("profiles.py", "audio.py"):
                continue
            with open(os.path.join(core, name), encoding="utf-8") as handle:
                source = handle.read()
            self.assertNotIn("import audio", source, name)
            self.assertNotIn(", audio", source, name)
            self.assertNotIn(".look", source, name)

    def test_the_audio_envelopes_are_bounded_smooth_and_repeatable(self):
        from procedural_disagreement.core import audio
        for band in ("low", "mid", "high", "rms"):
            previous = audio.level(band, 0.0)
            for i in range(1, 280 * 30):
                now = audio.level(band, i / 30.0)
                self.assertTrue(0.0 <= now <= 1.0)
                self.assertLess(abs(now - previous), 0.12)          # no frame-to-frame flicker
                previous = now
            self.assertEqual(audio.level(band, 123.456), audio.level(band, 123.456))
        self.assertEqual(audio.level("low", -1.0), 0.0)
        self.assertEqual(audio.level("low", 400.0), 0.0)
        # It follows the music: loud at the peak, quiet in the bass-out phrase and the coda.
        self.assertGreater(audio.level("low", 250.0), audio.level("low", 205.0) + 0.2)
        self.assertGreater(audio.level("low", 250.0), audio.level("low", 258.0) + 0.2)


class EmissionTests(unittest.TestCase):
    """Network emission, 3:00-3:20: presentation only, and it keeps to the film's rules."""

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.core import hinge, network, refrain
        from procedural_disagreement.presentation import emission
        cls.emission, cls.hinge, cls.network, cls.refrain = emission, hinge, network, refrain
        cls.pieces = list(enumerate(hinge.pieces()))

    def test_it_starts_at_the_junction_and_goes_outward_ring_by_ring(self):
        e = self.emission
        for index, piece in self.pieces:
            self.assertEqual(e.level(piece, index, 180.0), 0.0)                # nothing at or before 3:00.0
            self.assertEqual(e.level(piece, index, 150.0), 0.0)
        hub = self.network.hub()
        self.assertEqual(e.ring_of(*hub), 0)
        self.assertEqual([e.reached(ring) for ring in (0, 1, 4)], [180.0, 182.5, 190.0])
        # At any moment, everything lit is no further out than the ring just reached.
        for t in (181.0, 183.0, 187.6, 195.1, 200.0):
            lit = [e.part(piece, index)[1] for index, piece in self.pieces if e.level(piece, index, t) > 0.0]
            self.assertTrue(lit)
            self.assertLessEqual(max(lit), int((t - 180.0) / 2.5))
            self.assertEqual(min(lit), 0)
        # The junction is the clearest source, and the first.
        junction = [(index, piece) for index, piece in self.pieces if (e.part(piece, index) or ("",))[0] == "junction"]
        self.assertEqual(len(junction), 2)
        strongest = max(e.level(piece, index, 180.6) for index, piece in self.pieces)
        self.assertEqual(strongest, max(e.level(piece, index, 180.6) for index, piece in junction))
        # The source itself is the strongest thing in the passage: about twice an ordinary run.
        peak = lambda fn: max(fn(180.0 + i / 30.0) for i in range(601))
        everything = max(peak(lambda t, i=index, p=piece: e.level(p, i, t)) for index, piece in self.pieces[::3])
        self.assertEqual(e.source_level(180.0), 0.0)
        self.assertGreater(peak(e.source_level), everything)
        ordinary = 0.5 * (e.STRENGTH["trunk"][0] + e.STRENGTH["main"][0])
        self.assertTrue(1.75 <= e.SOURCE / ordinary <= 2.0)
        # What has been reached stays half awake: 3:20 keeps what the passage built.
        self.assertEqual(e.HOLD, 0.5)
        self.assertAlmostEqual(e.envelope(200.0, 180.0), 0.5, places=3)

    def test_it_never_touches_the_lane_and_only_ever_lights_routing(self):
        e = self.emission
        kinds = set()
        for index, piece in self.pieces:
            what = e.part(piece, index)
            if self.network.intrusion(piece) is not None:
                self.assertIsNone(what)                                        # nothing that lies in the lane
            if what is not None:
                kinds.add(piece.kind)
        self.assertEqual(kinds, {"trunk", "main", "via", "fine"})
        # Every trunk and main within reach carries a response; most fine runs stay dark.
        count = lambda kind: sum(1 for index, piece in self.pieces if piece.kind == kind)
        lit = lambda kind: sum(1 for index, piece in self.pieces if piece.kind == kind and e.part(piece, index))
        self.assertLess(lit("fine"), 0.2 * count("fine"))
        for index, piece in self.pieces:
            if piece.kind in ("trunk", "main") and self.network.intrusion(piece) is None                     and e.ring_of(piece.center[0], piece.center[1]) < e.RINGS:
                self.assertIsNotNone(e.part(piece, index))

    def test_it_is_bounded_smooth_and_repeatable(self):
        e = self.emission
        for index, piece in self.pieces[::7]:
            previous = 0.0
            for i in range(601):
                now = e.level(piece, index, 180.0 + i / 30.0)
                self.assertTrue(0.0 <= now <= 3.0)
                self.assertLess(abs(now - previous), 0.45)
                previous = now
            self.assertEqual(e.level(piece, index, 191.3), e.level(piece, index, 191.3))
            self.assertEqual(e.level(piece, index, 210.0), e.level(piece, index, 230.0))     # it holds; nothing later is designed
        for kit in self.refrain.kits() + self.refrain.later_kits():
            self.assertEqual(e.cell_level(kit, 180.0), 0.0)
            self.assertGreater(e.cell_level(kit, 180.0 + 2.5 * self.network.ring(kit) + 0.5), 0.0)   # on the film's own ring


class LaneEmissionTests(unittest.TestCase):
    """Network emission, 3:20-3:30: the routing beside the lane goes quiet. Presentation only."""

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.core import hinge, network, refrain
        from procedural_disagreement.presentation import emission
        cls.emission, cls.network, cls.refrain = emission, network, refrain
        cls.pieces = list(enumerate(hinge.pieces()))

    def test_nothing_changes_at_or_before_three_twenty(self):
        e = self.emission
        self.assertEqual(e.field(200.0), 1.0)
        for index, piece in self.pieces[::5]:
            self.assertEqual(e.lane_quiet(piece.center[0], piece.center[1], 200.0), 0.0)
            what = e.part(piece, index)
            if what:
                self.assertEqual(e.level(piece, index, 200.0), what[2] * e.envelope(200.0, e.reached(what[1])))

    def test_nothing_is_ever_lit_in_the_lane_and_the_routing_beside_it_goes_quiet(self):
        e, network = self.emission, self.network
        for index, piece in self.pieces:
            if network.intrusion(piece) is not None:
                for t in (201.0, 205.0, 210.0):
                    self.assertEqual(e.level(piece, index, t), 0.0)
        # By 3:30, routing within 16 m of the lane's axis keeps under a tenth of what it had,
        # and routing beyond 42 m keeps the whole field's share.
        near = far = 0
        for index, piece in self.pieces:
            if not e.part(piece, index):
                continue
            had = e.level(piece, index, 200.0)
            d = network.lane_distance(piece.center[0], piece.center[1])
            if d < e.QUIET_WITHIN:
                self.assertLess(e.level(piece, index, 210.0), 0.1 * had + 1e-9)
                near += 1
            elif d > e.QUIET_BEYOND:
                self.assertAlmostEqual(e.level(piece, index, 210.0), e.FIELD_KEPT * had, places=9)
                far += 1
        self.assertGreaterEqual(near, 5)           # few: most of what stood this near lies in the lane itself
        self.assertGreater(far, 100)
        # It goes quiet along the lane in the order the lane is cleared: the mouth first.
        mouth, end = network.lane_point(2.0), network.lane_point(55.0)
        self.assertGreater(e.lane_quiet(mouth[0], mouth[1], 201.0), e.lane_quiet(end[0], end[1], 201.0))
        self.assertEqual(e.lane_quiet(end[0], end[1], 201.0), 0.0)
        self.assertAlmostEqual(e.lane_quiet(end[0], end[1], 210.0), 1.0, places=6)

    def test_it_only_ever_goes_down_and_the_stations_facing_the_lane_keep_their_cells(self):
        e = self.emission
        for index, piece in self.pieces[::4]:
            previous = e.level(piece, index, 200.0)
            for i in range(1, 301):
                now = e.level(piece, index, 200.0 + i / 30.0)
                self.assertLessEqual(now, previous + 1e-9)             # nothing new lights between 3:20 and 3:30
                previous = now
        self.assertLess(e.source_level(210.0), 0.1 * e.source_level(200.0))            # the lane starts beside the junction
        for kit in self.refrain.kits() + self.refrain.later_kits():
            if self.network.beside_lane(kit):
                self.assertAlmostEqual(e.cell_level(kit, 210.0), e.FIELD_KEPT * e.cell_level(kit, 200.0), places=9)


class ProsthesisEmissionTests(unittest.TestCase):
    """Network emission, 3:30-4:00: the route and its three roles. Presentation only."""

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.core import hinge, network, prosthesis, refrain
        from procedural_disagreement.presentation import emission
        cls.emission, cls.hinge, cls.network, cls.prosthesis = emission, hinge, network, prosthesis
        cls.pieces = list(enumerate(hinge.pieces()))
        cls.kits = {kit.station: kit for kit in refrain.kits() + refrain.later_kits()}

    def test_nothing_changes_at_or_before_three_thirty(self):
        e = self.emission
        for t in (180.0, 200.0, 205.0, 210.0):
            self.assertEqual(e.cell_rest(t), 0.0)
            for kit in self.kits.values():
                self.assertEqual(e.cell_dim(kit, t), 0.0)
                self.assertEqual(e.acting(kit.station, t), 0.0)
            for index, piece in self.pieces[::9]:
                self.assertEqual(e.route_level(index, t), 0.0)

    def test_at_three_thirty_the_whole_field_goes_to_rest(self):
        e = self.emission
        self.assertEqual((e.CELL_REST, e.CELL_RESTS_OVER), (0.12, 1.25))               # approved: do not retune
        previous = 0.0
        for i in range(1, 61):
            now = e.cell_rest(210.0 + i / 30.0)
            self.assertGreaterEqual(now, previous)                                     # it only settles
            self.assertLess(now - previous, 0.08)                                      # and never steps
            previous = now
        self.assertEqual(e.cell_rest(211.25), 1.0)
        # Every station's cell, recruited or not, on the route or not: the same rest.
        at_rest = {round(e.cell_dim(kit, 211.24), 9) for kit in self.kits.values()}
        self.assertEqual(len(at_rest), 1)
        self.assertAlmostEqual(at_rest.pop(), 1.0 - e.CELL_REST, places=3)

    def test_a_donor_comes_to_full_a_receiver_goes_out_a_carrier_stays_at_rest(self):
        e, prosthesis = self.emission, self.prosthesis
        rest = 1.0 - e.CELL_REST
        for station, (role, when, _) in prosthesis.recruits().items():
            kit = self.kits[station]
            height = when + 2.2                                                        # the held height of its first stroke
            if height > 240.0:
                continue
            self.assertAlmostEqual(e.acting(station, height), 1.0, places=6)
            if role == prosthesis.DONOR:
                self.assertAlmostEqual(e.cell_dim(kit, height), 0.0, places=6)         # full: it gives
            elif role == prosthesis.RECEIVER:
                self.assertGreater(e.cell_dim(kit, height), 0.99)                      # out: it takes
            else:
                self.assertAlmostEqual(e.cell_dim(kit, height), rest, places=6)        # at rest: its verb is in the routing
            # Between strokes every one of them is at rest again.
            if when + 6.0 <= 240.0:                                                    # (nothing after 4:00 is designed)
                self.assertAlmostEqual(e.cell_dim(kit, when + 6.0), rest, places=6)
        # A station that is not on the route never leaves rest.
        for station, kit in self.kits.items():
            if station not in prosthesis.recruits():
                for t in (215.0, 225.0, 235.0, 240.0):
                    self.assertAlmostEqual(e.cell_dim(kit, t), rest, places=9)

    def test_a_carrier_and_the_relay_answer_in_the_routing_and_the_route_accumulates(self):
        e, prosthesis = self.emission, self.prosthesis
        blocks = {station: index for index, station in e._junction_blocks().items()}
        route = set(prosthesis.recruits()) | {prosthesis.RELAY_STATION}
        self.assertTrue(route <= set(blocks))
        for station in route:
            piece = self.hinge.pieces()[blocks[station]]
            self.assertIsNone(self.network.intrusion(piece))                           # none of it lies in the lane
            when = prosthesis.RELAY_BEGINS if station == prosthesis.RELAY_STATION else prosthesis.recruits()[station][1]
            self.assertEqual(e.route_level(blocks[station], when), 0.0)
            self.assertGreater(e.route_level(blocks[station], when + 0.6), 0.5)        # it comes up as its station joins
            self.assertGreaterEqual(e.route_level(blocks[station], 240.0), e.ROUTE * e.HOLD - 1e-6)     # and stays
        for station, (role, when, _) in prosthesis.recruits().items():
            if when + 2.2 > 240.0:
                continue
            pulse = e.route_level(blocks[station], when + 2.2) - e.ROUTE * e._later(when + 2.2, when)
            if role == prosthesis.CARRIER:
                self.assertAlmostEqual(pulse, e.CARRIER_PULSE, places=6)
            else:
                self.assertAlmostEqual(pulse, 0.0, places=9)
        # Lit in the order the film recruits: at any moment, exactly the stations recruited so far.
        for t in (212.0, 218.0, 223.0, 231.0, 239.0):
            lit = {station for station in route if e.route_level(blocks[station], t) > 0.0}
            due = {station for station, (_, when, _) in prosthesis.recruits().items() if when < t}
            if t > prosthesis.RELAY_BEGINS:
                due.add(prosthesis.RELAY_STATION)
            self.assertEqual(lit, due)
        # A junction block that belongs to no route station is as the lane passage left it.
        for index, piece in self.pieces:
            if piece.kind == "via" and e._junction_blocks().get(index) not in route:
                self.assertEqual(e.route_level(index, 230.0), 0.0)

    def test_what_has_just_joined_owns_the_picture(self):
        e, prosthesis = self.emission, self.prosthesis
        self.assertEqual(e.LATER_STROKES, 0.45)
        for station, (role, when, _) in prosthesis.recruits().items():
            if when + 7.5 + 2.2 > 240.0:
                continue
            first, later = e.acting(station, when + 2.2), e.acting(station, when + 7.5 + 2.2)
            self.assertAlmostEqual(first, 1.0, places=6)
            self.assertAlmostEqual(later, 0.45, places=6)                              # perceptible, and subordinate
        # Bounded and smooth, on the film's own clock, for the whole passage.
        for station in prosthesis.recruits():
            kit = self.kits[station]
            previous = e.cell_dim(kit, 210.0)
            for i in range(1, 901):
                now = e.cell_dim(kit, 210.0 + i / 30.0)
                self.assertTrue(0.0 <= now <= 1.0)
                if abs(now - previous) > 0.12:
                    # The only step allowed is the end of a station's first turn, where a repeat begins lower.
                    since = 210.0 + i / 30.0 - prosthesis.recruits()[station][1]
                    self.fail("station %d: its cell steps by %.2f, %.2f s after it was recruited" % (station, now - previous, since))
                previous = now


class ClimaxEmissionTests(unittest.TestCase):
    """Network emission, 4:00-4:15: the climax drives the marks the network already has."""

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.core import climax, hinge, network, prosthesis, refrain
        from procedural_disagreement.presentation import emission
        cls.emission, cls.climax, cls.network, cls.prosthesis = emission, climax, network, prosthesis
        cls.pieces = list(enumerate(hinge.pieces()))
        cls.lit = [(index, piece) for index, piece in cls.pieces if emission.part(piece, index)]
        cls.kits = {kit.station: kit for kit in refrain.kits() + refrain.later_kits()}

    def test_four_oclock_is_the_end_of_the_prosthesis_passage(self):
        e = self.emission
        frame = 1.0 / 30.0
        # Nothing steps across 4:00.0: routing, junction blocks and cells all go on from where they were.
        for index, piece in self.lit:
            self.assertLess(abs(e.level(piece, index, 240.0 + frame) - e.level(piece, index, 240.0)), 0.01)
        for kit in self.kits.values():
            before, at, after = (e.cell_dim(kit, 240.0 + k * frame) for k in (-1, 0, 1))
            self.assertLess(abs((after - at) - (at - before)), 0.02)                   # no kink, let alone a step
        self.assertEqual((e.climax_hold(240.0), e.climax_field(240.0)), (e.HOLD, e.FIELD_KEPT))

    def test_the_cell_grammar_is_exactly_the_approved_one(self):
        e, climax = self.emission, self.climax
        rest = 1.0 - e.CELL_REST
        for station, (role, when) in climax.recruits().items():
            kit = self.kits[station]
            for t in (240.5 + 0.25 * k for k in range(58)):
                stroke = e.acting(station, t)
                dim = e.cell_dim(kit, t)
                if role == climax.DONOR:
                    self.assertAlmostEqual(dim, rest * (1.0 - stroke), places=9)
                elif role == climax.RECEIVER:
                    self.assertAlmostEqual(dim, rest + (1.0 - rest) * e.RECEIVER_DIM * stroke, places=9)
                else:
                    self.assertAlmostEqual(dim, rest, places=9)
                # A cell's own glow is not part of the climax's accumulation.
                self.assertAlmostEqual(e.cell_level(kit, t), e.cell_level(kit, 239.0), places=9)
        # Every station with machinery takes part, each from its own authored moment.
        for station, (role, when) in climax.recruits().items():
            if when > 240.0:
                self.assertEqual(e.acting(station, when - 0.01), 0.0)
                self.assertGreater(e.acting(station, when + 1.0), 0.5)

    def test_it_spreads_from_the_lane_and_never_into_it_or_across_it(self):
        e, network = self.emission, self.network
        for index, piece in self.pieces:
            if network.intrusion(piece) is not None:
                for t in (241.0, 246.0, 251.0, 254.375, 254.9):
                    self.assertEqual(e.level(piece, index, t), 0.0)
        # Its clock is distance from the lane: nearer is reached first, on the beat.
        reached = sorted((network.lane_distance(*piece.center[:2]), e.spread_reaches(piece)) for index, piece in self.lit)
        self.assertEqual([when for _, when in reached], sorted(when for _, when in reached))
        # Every run the lane cut stops short of the cut, on its own side.
        ends = [piece for index, piece in self.pieces if e.cut_end(piece)]
        self.assertEqual(len(ends), 6)
        for piece in ends:
            axis, at, side = e.cut_end(piece)
            self.assertAlmostEqual(abs(at - piece.center[axis]), piece.size[axis] * 0.5, places=6)
            beyond = (piece.center[0], piece.center[1])
            beyond = list(beyond)
            beyond[axis] = at - side * 1.0
            self.assertLess(network.lane_distance(*beyond), network.lane_distance(*piece.center[:2]))   # the cut is toward the lane

    def test_structure_refreshes_and_never_exceeds_its_own_peak(self):
        e = self.emission
        for index, piece in self.lit:
            if piece.kind == "via":
                continue                                                               # junction blocks also carry the route
            peak = e.part(piece, index)[2]
            for t in (240.0 + 0.2 * k for k in range(76)):
                self.assertLessEqual(e.level(piece, index, t), peak + 1e-9)
            for begins in e.structural_stroke(piece) or ():
                # At the height of its rise a structural piece is back near its own peak.
                self.assertGreater(e.level(piece, index, begins + e.RISE), 0.8 * peak * e.climax_field(begins + e.RISE))

    def test_added_marks_are_admitted_by_their_wave_and_never_before_four(self):
        e, network, climax = self.emission, self.network, self.climax
        runs = [piece for index, piece in self.lit if piece.kind in ("trunk", "main")]
        for piece in runs:
            for layer in (0, 1):
                for t in (150.0, 239.99, 240.0):
                    self.assertEqual(e.dense(piece, layer, t), 0.0)
            coupling, saturation = e.dense_admitted(piece)
            self.assertGreaterEqual(coupling, climax.COUPLING)
            self.assertGreaterEqual(coupling, e.spread_reaches(piece))
            self.assertGreaterEqual(saturation, climax.SATURATION)
            self.assertEqual(e.dense(piece, 0, coupling), 0.0)
            self.assertEqual(e.dense(piece, 1, saturation), 0.0)
        # Outward from the lane: nearer runs are admitted no later than further ones.
        order = sorted((network.lane_distance(*piece.center[:2]), e.dense_admitted(piece)) for piece in runs
                       if network.lane_distance(*piece.center[:2]) <= e.CLIMAX_REACH)
        for layer in (0, 1):
            whens = [when[layer] for _, when in order]
            self.assertEqual(whens, sorted(whens))
        # Not at the boundary all at once: at 4:11.5 only the nearest are coming in.
        admitted = sum(1 for piece in runs if e.dense(piece, 1, 251.5) > 0.0)
        self.assertLess(admitted, 0.2 * sum(1 for piece in runs if e.dense(piece, 1, 254.375) > 0.0))
        # Nothing beyond the climax's reach and nothing in the lane.
        for index, piece in self.pieces:
            if piece.kind in ("trunk", "main") and (network.intrusion(piece) is not None
                                                    or network.lane_distance(*piece.center[:2]) > e.CLIMAX_REACH):
                self.assertEqual((e.dense(piece, 0, 254.375), e.dense(piece, 1, 254.375)), (0.0, 0.0))

    def test_fine_runs_widen_only_from_saturation(self):
        e, climax = self.emission, self.climax
        fine = [(index, piece) for index, piece in self.pieces if piece.kind == "fine"]
        answering = lambda t: sum(1 for index, piece in fine if e.level(piece, index, t) > 0.0)
        self.assertEqual(answering(251.2), answering(240.5))
        self.assertGreater(answering(254.375), 2 * answering(251.2))
        for index, piece in fine:
            if e.part(piece, index) is None and e.climax_part(piece, index):
                self.assertEqual(e.level(piece, index, climax.SATURATION), 0.0)

    def test_it_accumulates_by_holding_more_and_then_holds(self):
        e = self.emission
        total = lambda t: sum(e.level(piece, index, t) for index, piece in self.lit)
        self.assertGreater(total(254.375), 1.8 * total(240.0))
        self.assertLess(total(244.0), total(248.0))
        self.assertLess(total(248.0), total(254.375))
        # From the peak to 4:15 it holds: no flash at the end.
        self.assertLess(abs(total(254.967) - total(254.375)), 0.05 * total(254.375))
        blocks = lambda t: sum(1 for index, piece in self.pieces if piece.kind == "via" and e.route_level(index, t) > 0.02)
        self.assertEqual(blocks(239.9), 13)
        self.assertGreater(blocks(254.375), 3 * blocks(239.9))                          # occupancy, not brightness
        self.assertEqual((e.climax_hold(254.375), e.climax_field(254.375)), (0.85, 1.0))


class OuterFrameTests(unittest.TestCase):
    """0:00-0:35 and 4:25-4:40: the system before the case and after it."""

    FILM = (35.0, 35.0333, 40.0, 52.5, 60.0, 66.25, 70.0, 75.0, 80.0, 90.0, 96.9, 100.0, 112.4667, 200.0, 255.0)

    def setUp(self):
        self.p, self.a = variants.primary(), variants.alternate()
        self.fail_time = self.p.tower_fail_time

    def yaw(self, t):
        rotation = ch.reindex_head(self.p, t, self.fail_time)[1]
        return math.degrees(2.0 * math.atan2(rotation[3], rotation[0]))

    def state(self, t):
        """Everything the outer frame can move or change, at time t."""
        return (ch.camera_pose(t), ch.reindex_head(self.p, t, self.fail_time), ch.reindex_carriage(t),
                ch.receiver_offset(t), (ch.panel_attend(self.a, t), outer.opening_panel(t)), outer.conduit_open(t), outer.lamp_height(t),
                outer.clock(t), outer.coupling(t), outer.room_light(t), outer.zone_levels(t), outer.subject_presence(t))

    # ---- the locked film is untouched

    def test_the_first_locked_frame_is_exactly_what_it_was(self):
        t = timeline.SECTION_START
        self.assertEqual(ch.camera_pose(t), ch._film_camera(t))
        self.assertEqual(ch.camera_pose(t)[0], layout.CAMERA_START)
        self.assertEqual(ch.reindex_head(self.p, t, self.fail_time), ch.head_pose(self.p, t, self.fail_time))
        self.assertEqual(ch.reindex_head(self.p, t, self.fail_time), ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0)))
        self.assertEqual(ch.reindex_carriage(t), (0.0, 0.0))
        self.assertEqual(ch.receiver_offset(t), ch.disposal_carriage(t))
        self.assertEqual(ch.panel_attend(self.a, t), (1.0, 0.0, 0.0, 0.0))
        self.assertEqual((outer.conduit_open(t), outer.lamp_height(t), outer.opening_panel(t)), (0.0, 0.0, 0.0))
        self.assertEqual((outer.clock(t), outer.coupling(t), outer.subject_presence(t)), (t, 1.0, 1.0))
        self.assertEqual(outer.light((0.0,) * 7, t), 1.0)
        self.assertEqual(outer.light((1.0,) * 7, t), 1.0)

    def test_inside_the_film_the_outer_frame_is_exactly_neutral(self):
        for t in self.FILM:
            self.assertEqual(outer.clock(t), t)
            self.assertEqual((outer.coupling(t), outer.room_light(t), outer.subject_presence(t)), (1.0, 1.0, 1.0))
            self.assertEqual((outer.conduit_open(t), outer.lamp_height(t)), (0.0, 0.0))
            self.assertEqual(ch.camera_pose(t), ch._film_camera(t))
            self.assertEqual(ch.receiver_offset(t), ch.disposal_carriage(t))
            self.assertEqual(ch.presence(self.a, t) > 0.0, t >= 45.1)

    def test_the_opening_arrives_at_rest_and_the_camera_arrives_at_speed(self):
        # Every stroke of the opening is over well before 0:35...
        at = self.state(35.0)
        for t in (32.0, 33.5, 34.9667):
            now = self.state(t)
            self.assertEqual(now[1:7], at[1:7])
            self.assertEqual(now[8:], at[8:])
        # ...and the camera joins the approach with the approach's own velocity and lens.
        dt = 1.0 / timeline.FPS
        before = sub(ch.camera_pose(35.0)[0], ch.camera_pose(35.0 - dt)[0])
        after = sub(ch.camera_pose(35.0 + dt)[0], ch.camera_pose(35.0)[0])
        self.assertLess(length(sub(before, after)), 2e-6)
        self.assertAlmostEqual(ch.camera_pose(35.0)[2] - ch.camera_pose(35.0 - dt)[2],
                               ch.camera_pose(35.0 + dt)[2] - ch.camera_pose(35.0)[2], places=6)
        for i in range(1, 1050):
            step = length(sub(ch.camera_pose(i * dt)[0], ch.camera_pose((i - 1) * dt)[0]))
            self.assertLess(step, 0.016)                 # under half a metre a second, always

    # ---- the opening

    def test_the_opening_is_cued_to_its_transients_in_order(self):
        cues = [outer.OPENING_HEAD, outer.OPENING_CARRIAGE, outer.OPENING_TRAY, outer.OPENING_PANEL, outer.OPENING_BODY,
                outer.OPENING_SHOULDER, outer.OPENING_COUPLE_START, outer.OPENING_COUPLE, outer.OPENING_SEAT,
                outer.OPENING_READY]
        self.assertEqual(cues, sorted(cues))
        self.assertLess(cues[-1], outer.OPENING_END)
        self.assertLess(outer.OPENING_SHOULDER, outer.OPENING_COUPLE)

    def test_it_begins_dark_and_each_hit_lights_one_place(self):
        centres = [outer.zone_weights(centre) for _, centre, _ in outer.zones()]
        for weights in centres:
            self.assertEqual(outer.light(weights, 0.0), 0.0)
        hits = (outer.OPENING_HEAD, outer.OPENING_CARRIAGE, outer.OPENING_TRAY, outer.OPENING_PANEL, outer.OPENING_BODY,
                outer.OPENING_SHOULDER)
        for index, hit in enumerate(hits):
            self.assertLess(outer.light(centres[index], hit), 0.05)
            self.assertEqual(outer.light(centres[index], hit + 0.5), 1.0)
        # The body is not lit until the fifth hit, and its shoulders not until the sixth.
        self.assertEqual(outer.light(centres[4], outer.OPENING_PANEL + 2.0), 0.0)
        self.assertLess(outer.light(centres[5], outer.OPENING_BODY + 2.0), 0.05)
        # Far from every pool there is nothing until the system couples.
        self.assertEqual(outer.light(outer.zone_weights((-6.0, -10.0, 3.0)), 19.9), 0.0)
        self.assertGreater(outer.light(outer.zone_weights((-6.0, -10.0, 3.0)), 23.0), 0.2)
        self.assertLess(outer.light(outer.zone_weights((-6.0, -10.0, 3.0)), 29.9), 0.5)

    def test_the_head_faces_the_body_before_the_body_is_lit(self):
        tower, shoulder = layout.tower_position(1), outer.EMPTY_COORDINATE
        to_body = math.degrees(math.atan2(shoulder[0] - tower[0], tower[1] - shoulder[1]))
        self.assertAlmostEqual(self.yaw(0.0), outer.HEAD_PARKED_YAW)
        self.assertAlmostEqual(self.yaw(outer.OPENING_BODY), to_body)
        self.assertAlmostEqual(self.yaw(outer.OPENING_SEAT), to_body)
        self.assertAlmostEqual(self.yaw(outer.OPENING_SEAT + 1.5), 0.0)
        self.assertEqual(ch.reindex_head(self.p, 0.0, self.fail_time)[0][2], outer.HEAD_PARKED_LIFT)

    def test_the_system_couples_on_the_bass_entry(self):
        self.assertEqual(outer.conduit_open(outer.OPENING_COUPLE_START), outer.CONDUIT_OPEN)
        self.assertEqual(outer.conduit_open(outer.OPENING_COUPLE), 0.0)
        for t in (0.0, 10.0, outer.OPENING_COUPLE):
            self.assertEqual(outer.coupling(t), 0.0)
            self.assertEqual(outer.clock(t), outer.clock(0.0))
            self.assertEqual(ch.conduit_energy(0.3, t, ch.NEVER, 1.0), 0.0)
            self.assertEqual(ch.rotor_angle(self.p, t, self.fail_time), ch.rotor_angle(self.p, 0.0, self.fail_time))
        # It runs up evenly and is exactly the track's own clock four seconds later.
        previous = outer.clock(outer.OPENING_COUPLE)
        for i in range(1, 125):
            now = outer.clock(outer.OPENING_COUPLE + i / 30.0)
            self.assertGreater(now, previous)
            self.assertLessEqual(now - previous, 1.0 / 30.0 + 1e-9)
            previous = now
        self.assertEqual(outer.clock(24.01), 24.01)

    def test_ready_is_the_lamp_docking_and_the_light_coming_up(self):
        self.assertEqual(outer.lamp_height(outer.OPENING_READY), outer.LAMP_RAISED)
        self.assertEqual(outer.lamp_height(outer.OPENING_READY + 0.9), 0.0)
        self.assertLess(outer.room_light(outer.OPENING_READY), 0.5)
        self.assertEqual(outer.room_light(outer.OPENING_READY + 1.5), 1.0)

    # ---- the ending

    def test_the_required_state_at_four_twenty_five(self):
        t = outer.ENDING_START
        self.assertEqual(t, 265.0)
        self.assertEqual((outer.subject_presence(t), outer.alternates_presence(t), outer.coupling(t)), (0.0, 0.0, 0.0))
        self.assertEqual(ch.presence(self.a, t), 0.0)
        self.assertEqual(ch.system_branch_presence(t), 0.0)
        self.assertFalse(ch.camera_is_below(t))
        self.assertEqual(outer.lamp_height(t), outer.LAMP_RAISED_ENDING)
        # The apparatus is as the film left it: the accepted arrangement of 1:20.
        for now, then in zip(ch.reindex_carriage(t), ch.reindex_carriage(100.0)):
            self.assertAlmostEqual(now, then, places=12)
        self.assertEqual(ch.reindex_head(self.p, t, self.fail_time)[0], ch.reindex_head(self.p, 100.0, self.fail_time)[0])
        self.assertAlmostEqual(self.yaw(t), self.yaw(100.0))
        self.assertEqual(outer.conduit_open(t), 0.0)

    def test_the_ending_is_seen_from_where_the_film_began(self):
        first = ch.camera_pose(0.0)
        for t in (265.0, 270.0, 276.3, 280.0):
            self.assertEqual(ch.camera_pose(t), first)
        self.assertEqual(first[0], layout.OUTER_CAMERA_POSITION)

    def test_the_apparatus_turns_to_the_empty_coordinate(self):
        tower, empty = layout.tower_position(1), outer.EMPTY_COORDINATE
        self.assertEqual(empty, layout.arm_origin(1))
        to_empty = math.degrees(math.atan2(empty[0] - tower[0], tower[1] - empty[1]))
        self.assertAlmostEqual(self.yaw(outer.ENDING_HEAD + 1.5), to_empty)
        # The same heading it took toward the body in the opening.
        self.assertAlmostEqual(self.yaw(outer.ENDING_HEAD + 1.5), self.yaw(outer.OPENING_BODY))
        slide, extension = ch.reindex_carriage(outer.ENDING_CONFIRM)
        self.assertAlmostEqual(slide, 0.75)
        self.assertAlmostEqual(extension, 0.5)
        self.assertEqual(outer.lamp_height(outer.ENDING_CONFIRM + 0.5), 0.0)

    def test_the_hits_come_further_apart_and_then_nothing_moves(self):
        hits = [outer.ENDING_HEAD, outer.ENDING_CARRIAGE, outer.ENDING_CONFIRM]
        self.assertGreater(hits[2] - hits[1], hits[1] - hits[0])
        self.assertLessEqual(outer.LAST_MOTION, outer.ENDING_SILENCE)
        still = self.state(outer.ENDING_END)
        for i in range(0, 112):
            self.assertEqual(self.state(outer.ENDING_SILENCE + i / 30.0), still)
        # It is not dark: the room is dim and three places are fully lit.
        self.assertGreater(outer.room_light(280.0), 0.2)
        levels = dict(zip([name for name, _, _ in outer.zones()], outer.zone_levels(280.0)))
        self.assertEqual({name for name, level in levels.items() if level == 1.0}, {"head", "carriage", "plinth", "lamp"})


class ReindexTests(unittest.TestCase):
    """1:10-1:20: the room measures its new state and accepts it."""

    def setUp(self):
        self.p = variants.primary()
        self.fail = self.p.tower_fail_time

    def head(self, t):
        return ch.reindex_head(self.p, t, self.fail)

    def yaw(self, t):
        rotation = self.head(t)[1]
        return math.degrees(2.0 * math.atan2(rotation[3], rotation[0]))

    def test_one_stroke_per_bar_inside_the_reopened_phrase(self):
        cues = [timeline.REINDEX_FIRST, timeline.REINDEX_SECOND, timeline.REINDEX_CROSSCHECK, timeline.REINDEX_ACCEPT]
        self.assertEqual(cues, [70.0, 72.5, 75.0, 77.5])
        self.assertLess(ch.REINDEX_END, timeline.ABSENT_ATTRACTOR - 0.5)

    def test_nothing_before_the_first_index_is_touched(self):
        for t in (35.0, 52.5, 56.0, 57.0, 60.0, 66.25, 69.0, 69.9667, 70.0):
            self.assertEqual(self.head(t), ch.head_pose(self.p, t, self.fail))
            self.assertEqual(ch.reindex_carriage(t), (0.0, 0.0))

    def test_everything_is_at_rest_before_the_absent_attractor(self):
        rest_head, rest_carriage = self.head(ch.REINDEX_END), ch.reindex_carriage(ch.REINDEX_END)
        for t in (79.5, 80.0, 85.0, 90.0, 100.0, timeline.TIMELINE_END):
            self.assertEqual(self.head(t), rest_head)
            self.assertEqual(ch.reindex_carriage(t), rest_carriage)

    def test_the_accepted_state_is_not_the_old_one(self):
        fallen_lift, fallen = ch.head_pose(self.p, 69.0, self.fail)
        lift, rotation = self.head(80.0)
        self.assertGreater(abs(lift[2] - fallen_lift[2]), 0.05)
        self.assertGreater(abs(self.yaw(80.0) - self.yaw(69.0)), 5.0)
        self.assertAlmostEqual(abs(rotation[1]) + abs(rotation[2]), 0.0)        # level: it no longer tips
        slide, extension = ch.reindex_carriage(80.0)
        self.assertGreater(slide, 0.1)
        self.assertGreater(extension, 0.05)
        # ...but it is a small residue of much larger strokes.
        self.assertLess(slide, 0.3 * 0.75 + 1e-9)
        self.assertLess(extension, 0.3 * 0.5)

    def test_the_actions_come_in_order(self):
        # Bar 1: only the head moves. It ends facing the shoulder the arm was removed from.
        self.assertEqual(ch.reindex_carriage(timeline.REINDEX_SECOND), (0.0, 0.0))
        tower, shoulder = layout.tower_position(1), layout.arm_origin(1)
        facing = q_rotate(self.head(timeline.REINDEX_SECOND)[1], (0.0, -1.0, 0.0))
        toward = normalize((shoulder[0] - tower[0], shoulder[1] - tower[1], 0.0))
        self.assertAlmostEqual(dot(facing, toward), 1.0, places=6)
        # Bar 2: only the carriage moves.
        self.assertEqual(self.head(timeline.REINDEX_SECOND), self.head(timeline.REINDEX_CROSSCHECK))
        self.assertAlmostEqual(ch.reindex_carriage(timeline.REINDEX_CROSSCHECK)[0], 0.75)
        self.assertEqual(ch.reindex_carriage(timeline.REINDEX_CROSSCHECK)[1], 0.0)
        # Bar 3: the head turns to the carriage, and the carriage extends only after it has started.
        self.assertEqual(ch.reindex_carriage(timeline.REINDEX_CROSSCHECK + 0.6)[1], 0.0)
        self.assertNotEqual(self.head(timeline.REINDEX_CROSSCHECK + 0.6), self.head(timeline.REINDEX_CROSSCHECK))
        top = ch.reindex_carriage_top(timeline.REINDEX_ACCEPT)
        facing = q_rotate(self.head(timeline.REINDEX_ACCEPT)[1], (0.0, -1.0, 0.0))
        toward = normalize((top[0] - tower[0], top[1] - tower[1], 0.0))
        self.assertAlmostEqual(dot(facing, toward), 1.0, places=6)
        self.assertAlmostEqual(ch.reindex_carriage(timeline.REINDEX_ACCEPT)[1], 0.5)

    def test_every_stroke_is_smooth_and_never_reverses_within_itself(self):
        previous_yaw, previous = self.yaw(70.0), ch.reindex_carriage(70.0)
        for i in range(1, 301):
            t = 70.0 + i / 30.0
            yaw, carriage = self.yaw(t), ch.reindex_carriage(t)
            self.assertLess(abs(yaw - previous_yaw), 2.6)                      # degrees per frame
            self.assertLess(abs(carriage[0] - previous[0]), 0.035)             # metres per frame
            self.assertLess(abs(carriage[1] - previous[1]), 0.035)
            previous_yaw, previous = yaw, carriage
        slides = [ch.reindex_carriage(72.5 + i / 30.0)[0] for i in range(60)]
        self.assertEqual(slides, sorted(slides))

    def test_only_the_solid_reality_is_reindexed(self):
        for v in (variants.alternate(), variants.system_branch(), variants.extra_alternate(1)):
            for t in (71.0, 76.0, 80.0):
                self.assertEqual(ch.reindex_head(v, t, v.tower_fail_time), ch.head_pose(v, t, v.tower_fail_time))

    def test_the_carriage_is_a_cabinet_that_was_always_there(self):
        x, y, height = ch.reindex_carriage_rest()
        self.assertEqual((x, y, height), (layout.CABINET_X, *layout.cabinet(timeline.SEED, 6, 1)[:2]))
        # It runs toward the body's line and stays clear of the rib that is recruited at 1:30.
        self.assertLess(ch.reindex_carriage_top(75.0)[1], y)
        self.assertLess(y + 0.5, layout.RECRUITED_RIB_Y - 0.15)


class AbsentAttractorTests(unittest.TestCase):
    """The room organises itself around the place where the limb is not."""

    def setUp(self):
        self.a = variants.alternate()
        self.cue = timeline.ABSENT_ATTRACTOR
        self.end = self.cue + 4 * timeline.BAR

    @staticmethod
    def degrees(q):
        return math.degrees(2.0 * math.acos(min(1.0, abs(q[0]))))

    def responses(self, t):
        a = self.a
        return [ch.conduit_end_aim(a, t), ch.tower_head_aim(a, t), ch.panel_attend(a, t)]

    def test_nothing_responds_before_the_cue(self):
        for t in (timeline.SECTION_START, 66.25, 70.0, self.cue):
            for q in self.responses(t):
                self.assertAlmostEqual(self.degrees(q), 0.0, places=5)
            self.assertEqual(ch.attractor_progress(t), 0.0)

    def test_responses_start_one_after_another_and_arrive_together(self):
        a, bar = self.a, timeline.BAR
        early = self.cue + 0.9 * bar
        self.assertGreater(self.degrees(ch.conduit_end_aim(a, early)), 0.05)
        self.assertEqual(self.degrees(ch.tower_head_aim(a, early)), 0.0)
        self.assertEqual(self.degrees(ch.panel_attend(a, self.cue + 2.9 * bar)), 0.0)
        self.assertGreater(self.degrees(ch.tower_head_aim(a, self.cue + 2.0 * bar)), 0.05)
        for q, later in zip(self.responses(self.end), self.responses(self.end + 2.0)):
            self.assertGreater(self.degrees(q), 1.0)
            self.assertEqual(q, later)          # kept, not resolved back to neutral

    def test_nothing_snaps_or_reverses(self):
        frame = 1.0 / timeline.FPS
        previous = [0.0] * 3
        for i in range(int(12.5 * timeline.FPS)):
            now = [self.degrees(q) for q in self.responses(self.cue + i * frame)]
            for before, after in zip(previous, now):
                self.assertGreaterEqual(after, before - 1e-9)
                self.assertLess(after - before, 0.4)    # degrees per frame
            previous = now

    def test_every_response_implies_the_same_empty_point(self):
        from procedural_disagreement.core.vec import add, dot, mul, normalize, q_rotate
        a, point = self.a, ch.attractor_point(self.a)
        drift = ch.reality_offset(a, self.end)

        def miss(origin, direction, target):
            d = normalize(direction)
            v = sub(target, origin)
            return length(sub(v, mul(d, dot(v, d))))

        def flat(p):
            return (p[0], p[1], 0.0)

        path = layout.conduit_path(a.side)
        run = q_rotate(ch.conduit_end_aim(a, self.end), sub(path[0], path[1]))
        self.assertLess(miss(add(path[1], drift), run, point), 1e-6)

        head = add(add(layout.tower_position(a.side), (0.0, 0.0, layout.TOWER_HEAD_HEIGHT + 0.3)), drift)
        self.assertLess(miss(head, q_rotate(ch.tower_head_aim(a, self.end), (0.0, -1.0, 0.0)), point), 1e-6)

        panel = layout.back_panel_center(*layout.ATTRACTOR_PANEL)
        normal = q_rotate(ch.panel_attend(a, self.end), (0.0, -1.0, 0.0))
        self.assertLess(miss(panel, normal, point), 1e-6)   # in three dimensions

    def test_locus_comes_from_the_phantom_chain_not_the_removed_piece(self):
        a = self.a
        # The locus moves; the removed piece and the phantom load do not.
        self.assertGreater(length(sub(ch.phantom_locus(a, self.end), ch.phantom_locus(a, self.cue))), 0.15)
        self.assertEqual(ch.detach_pose(a, self.cue), ch.detach_pose(a, self.end))
        self.assertEqual(ch.phantom_load(a, self.cue), ch.phantom_load(a, self.end))
        self.assertEqual(ch.stump_pose(a, self.cue), ch.stump_pose(a, self.end))
        self.assertEqual(ch.tower_lean(a, self.cue), ch.tower_lean(a, self.end))
        self.assertEqual(ch.conduit_displacement(a, 0.5, self.cue), ch.conduit_displacement(a, 0.5, self.end))

    def test_one_responder_is_outside_the_phantom_load_chain(self):
        # The back-wall panel: solid, on the far wall, driven by nothing else.
        self.assertGreater(self.degrees(ch.panel_attend(self.a, self.end)), 10.0)

    def test_camera_is_completely_still_through_the_passage(self):
        held = ch.camera_pose(self.cue)
        frame = 1.0 / timeline.FPS
        for i in range(int((timeline.DISPOSAL_TRANSPORT - self.cue) * timeline.FPS) + 1):
            self.assertEqual(ch.camera_pose(self.cue + i * frame), held)

    def test_camera_arrives_at_the_hold_without_a_jump(self):
        # It has already come to rest before the cue: no velocity to cancel at 1:20.
        frame = 1.0 / timeline.FPS
        for i in range(1, 60):
            self.assertEqual(ch.camera_pose(self.cue - i * frame), ch.camera_pose(self.cue))


class ProstheticRecruitmentTests(unittest.TestCase):
    """One solid rib begins to move as the distal segment of the missing limb."""

    def setUp(self):
        self.a = variants.alternate()
        self.cue = timeline.PROSTHETIC_RECRUITMENT
        self.delay = 2.0 * timeline.BEAT

    @staticmethod
    def degrees(q):
        return math.degrees(2.0 * math.acos(min(1.0, abs(q[0]))))

    def stump(self, t):
        from procedural_disagreement.core.vec import q_conj, q_mul
        return self.degrees(q_mul(q_conj(ch.stump_pose(self.a, self.cue)), ch.stump_pose(self.a, t)))

    def rib(self, t):
        return self.degrees(ch.recruited_rotation(self.a, t))

    def test_nothing_before_the_cue_and_everything_earlier_is_untouched(self):
        a = self.a
        for t in (66.25, 80.0, 89.0, self.cue):
            self.assertEqual(ch.recruitment_gesture(t), 0.0)
            self.assertEqual(ch.recruited_rotation(a, t), (1.0, 0.0, 0.0, 0.0))
        # The gesture changes neither the phantom load nor what the room converged on.
        late = self.cue + 2.0
        self.assertEqual(ch.phantom_load(a, late), ch.phantom_load(a, self.cue))
        self.assertEqual(ch.tower_lean(a, late), ch.tower_lean(a, self.cue))
        self.assertEqual(ch.detach_pose(a, late), ch.detach_pose(a, self.cue))
        self.assertEqual(ch.panel_attend(a, late), ch.panel_attend(a, self.cue))
        self.assertEqual(ch.tower_head_aim(a, late), ch.tower_head_aim(a, self.cue))

    def test_the_body_moves_first_and_the_rib_answers_two_beats_later(self):
        self.assertGreater(self.stump(self.cue + 0.6), 2.0)
        self.assertEqual(self.rib(self.cue + self.delay), 0.0)
        self.assertGreater(self.rib(self.cue + self.delay + 0.6), 2.0)

    def test_stump_stays_small_and_the_rib_is_the_forearm(self):
        peak = self.cue + 2.0 * timeline.BEAT
        self.assertGreater(self.stump(peak), 8.0)
        self.assertLess(self.stump(peak), 9.0)
        # The rib's rotation is exactly a fixed fraction of what the phantom forearm has done, delayed.
        from procedural_disagreement.core.vec import Q_IDENTITY, q_conj, q_mul, q_slerp
        for dt in (1.0, 2.5, 4.0, 6.0, 9.0):
            t = self.cue + self.delay + dt
            forearm = q_mul(ch.phantom_forearm(self.a, t - self.delay), q_conj(ch.phantom_forearm(self.a, self.cue)))
            self.assertEqual(ch.recruited_rotation(self.a, t), q_slerp(Q_IDENTITY, forearm, ch.RECRUIT_GAIN))
            self.assertAlmostEqual(self.rib(t), ch.RECRUIT_GAIN * self.degrees(forearm), places=4)

    def test_the_rib_keeps_its_extent_while_the_body_gesture_grows(self):
        peak_rib = max(self.rib(self.cue + i / 30.0) for i in range(int(12.5 * 30)))
        self.assertAlmostEqual(peak_rib, 7.5, places=2)

    def test_the_shoulder_turns_about_its_socket(self):
        a, peak = self.a, self.cue + 2.0 * timeline.BEAT
        # Before the cue nothing in the shoulder assembly has moved.
        self.assertEqual(ch.stump_shift(a, self.cue), (0.0, 0.0, 0.0))
        self.assertEqual(ch.socket_swing(a, (0.0, 0.0, -0.085), self.cue), (0.0, 0.0, -0.085))
        # At the peak the ball has swung a little, and much less than the stump tip.
        ball = length(sub(ch.socket_swing(a, (0.0, 0.0, -0.085), peak), (0.0, 0.0, -0.085)))
        self.assertGreater(ball, 0.01)
        self.assertLess(ball, 0.04)
        # Nothing of the kind for realities without a phantom.
        self.assertEqual(ch.stump_shift(variants.primary(), peak), (0.0, 0.0, 0.0))

    def test_it_is_a_brief_bridge_of_one_correspondence(self):
        beat = timeline.BEAT
        # Stump: out by beat 2, held to beat 4, settled by beat 6. No second articulation.
        self.assertAlmostEqual(ch.recruitment_gesture(self.cue + 2 * beat), 1.0)
        self.assertAlmostEqual(ch.recruitment_gesture(self.cue + 4 * beat), 1.0)
        self.assertAlmostEqual(ch.recruitment_gesture(self.cue + 6 * beat), ch.RECRUIT_RESIDUE)
        self.assertAlmostEqual(ch.recruitment_gesture(timeline.TIMELINE_END), ch.RECRUIT_RESIDUE)
        # Rib: the same shape two beats on, and done before the second line of the lyric is over.
        self.assertGreater(self.rib(self.cue + 4 * beat), 7.0)
        self.assertAlmostEqual(self.rib(self.cue + 9 * beat), self.rib(timeline.TIMELINE_END), places=6)
        self.assertLess(self.cue + 9 * beat, timeline.LANDFILL)

    def test_it_settles_to_a_residue_of_about_a_fifth(self):
        end = timeline.TIMELINE_END
        peak_rib = max(self.rib(self.cue + i / 30.0) for i in range(int(12.5 * 30)))
        peak_stump = max(self.stump(self.cue + i / 30.0) for i in range(int(12.5 * 30)))
        self.assertAlmostEqual(self.rib(end) / peak_rib, 0.2, places=2)
        self.assertAlmostEqual(self.stump(end) / peak_stump, 0.2, places=2)
        self.assertEqual(self.rib(end), self.rib(end - 1.0))

    def test_no_snapping(self):
        previous = 0.0
        for i in range(int(12.5 * 30)):
            now = self.rib(self.cue + i / 30.0)
            self.assertLess(abs(now - previous), 0.4)   # degrees per frame
            previous = now

    def test_the_recruited_rib_exists(self):
        # Rib responses configured at positions where no rib stands silently do nothing.
        self.assertIn(layout.RECRUITED_RIB_Y, layout.rib_ys())

    def test_only_the_alternate_recruits_and_the_camera_stays_held(self):
        for v in (variants.primary(), variants.system_branch()):
            self.assertEqual(ch.recruited_rotation(v, self.cue + 3.0), (1.0, 0.0, 0.0, 0.0))
        # Still held through the whole of the bridge's first statement and the rib's answer.
        self.assertEqual(ch.camera_pose(self.cue), ch.camera_pose(timeline.DISPOSAL_TRANSPORT))


class DisposalTests(unittest.TestCase):
    """The removed parts are processed as waste; the phantom machinery carries on regardless."""

    def setUp(self):
        self.p, self.a = variants.primary(), variants.alternate()

    def world(self, v, t):
        """World position of a removed region's pivot (its cut end)."""
        from procedural_disagreement.core.vec import add, q_rotate
        limb = layout.arm_rotation(v.side)
        return add(add(layout.arm_cut_point(v.side, v.cut_index), ch.reality_offset(v, t)),
                   q_rotate(limb, ch.detach_pose(v, t)[0]))

    def test_cues_follow_the_lyric_in_order(self):
        times = [timeline.PROSTHETIC_RECRUITMENT, timeline.DISPOSAL_HANDLING, timeline.DISPOSAL_TRANSPORT,
                 timeline.LANDFILL, timeline.DISPOSAL_SEALED]
        self.assertEqual(times, sorted(times))
        self.assertEqual(timeline.LANDFILL, 96.25)

    def test_nothing_is_handled_before_its_cue(self):
        for v in (self.p, self.a):
            self.assertEqual(ch.detach_pose(v, timeline.DISPOSAL_HANDLING), ch.detach_pose(v, 80.0))
        for t in (35.0, 66.25, 90.0, timeline.DISPOSAL_TRANSPORT):
            self.assertEqual(ch.disposal_carriage(t), (0.0, 0.0, 0.0))
            self.assertEqual(ch.disposal_aperture(t), 0.0)

    def test_the_forearm_is_set_down_on_the_tray_before_the_tray_moves(self):
        placed = self.world(self.a, timeline.DISPOSAL_TRANSPORT)
        self.assertAlmostEqual(length(sub(placed, layout.DISPOSAL_FOREARM_POSITION)), 0.0, places=6)
        # It was hanging a metre or so above, and it has been turned through a right angle.
        self.assertGreater(length(sub(self.world(self.a, timeline.DISPOSAL_HANDLING), placed)), 1.0)
        from procedural_disagreement.core.vec import q_conj, q_mul
        before = ch.detach_pose(self.a, timeline.DISPOSAL_HANDLING)[1]
        after = ch.detach_pose(self.a, timeline.DISPOSAL_TRANSPORT)[1]
        turned = math.degrees(2.0 * math.acos(min(1.0, abs(q_mul(q_conj(before), after)[0]))))
        self.assertAlmostEqual(turned, 90.0, places=3)

    def test_both_removed_parts_ride_the_receiver_exactly(self):
        for t in (94.5, 95.625, 96.4, ch.disposal_threshold_time()):
            carriage = ch.disposal_carriage(t)
            for v in (self.p, self.a):
                moved = sub(self.world(v, t), self.world(v, timeline.DISPOSAL_TRANSPORT))
                self.assertAlmostEqual(length(sub(moved, carriage)), 0.0, places=6)

    def test_the_aperture_is_open_before_the_drop_and_shut_after(self):
        self.assertEqual(ch.disposal_aperture(timeline.LANDFILL), 1.0)
        self.assertEqual(ch.disposal_aperture(timeline.LANDFILL - timeline.BEAT), 1.0)
        self.assertEqual(ch.disposal_aperture(timeline.DISPOSAL_SEALED), 0.0)
        self.assertEqual(ch.disposal_aperture(timeline.TIMELINE_END), 0.0)
        # The receiver has arrived, and waits a beat over the open floor.
        arrived = ch.disposal_carriage(timeline.LANDFILL - timeline.BEAT)
        self.assertEqual(arrived, layout.DISPOSAL_ROUTE)

    def test_the_threshold_is_crossed_within_the_beat_of_landfill_and_for_good(self):
        crossed = ch.disposal_threshold_time()
        self.assertGreater(crossed, timeline.LANDFILL)
        self.assertLess(crossed, timeline.LANDFILL + timeline.BEAT)
        # Inside the word, on the measured lyric timing.
        self.assertGreater(crossed, 96.1)
        self.assertLess(crossed, 98.0)
        previous = 0.0
        for i in range(int((timeline.TIMELINE_END - timeline.LANDFILL) * timeline.FPS)):
            down = ch.disposal_drop(timeline.LANDFILL + i / timeline.FPS)
            self.assertGreaterEqual(down, previous)
            previous = down
        # The receiver itself stops just under the floor, hidden in the chute.
        parked = ch.disposal_carriage(timeline.TIMELINE_END)[2]
        self.assertLess(parked, -layout.DISPOSAL_LOAD_TOP)
        self.assertGreater(layout.RECEIVER_POSITION[2] + parked, layout.LANDFILL_CHUTE_BOTTOM)
        self.assertGreater(layout.DISPOSAL_DROP, layout.DISPOSAL_LOAD_TOP)

    def test_the_phantom_machinery_is_untouched_by_the_disposal(self):
        a = self.a
        before, after = timeline.DISPOSAL_HANDLING, timeline.TIMELINE_END
        self.assertEqual(ch.phantom_load(a, before), ch.phantom_load(a, after))
        self.assertEqual(ch.tower_lean(a, before), ch.tower_lean(a, after))
        self.assertEqual(ch.conduit_end_aim(a, before), ch.conduit_end_aim(a, after))
        self.assertEqual(ch.tower_head_aim(a, before), ch.tower_head_aim(a, after))
        self.assertEqual(ch.panel_attend(a, before), ch.panel_attend(a, after))
        # The phantom hand is still where the body left it, in the chamber. The forearm is
        # more than twenty metres below.
        locus = ch.phantom_locus(a, after)
        self.assertGreater(locus[2], 2.5)
        self.assertGreater(length(sub(locus, self.world(a, after))), 20.0)
        # And the recruited rib keeps its residue.
        self.assertGreater(math.degrees(2.0 * math.acos(min(1.0, abs(ch.recruited_rotation(a, after)[0])))), 1.0)

    def test_camera_leaves_its_hold_smoothly_when_the_transport_starts(self):
        frame = 1.0 / timeline.FPS
        start = timeline.DISPOSAL_TRANSPORT
        self.assertEqual(ch.camera_pose(start), ch.camera_pose(start - 5.0))
        first = length(sub(ch.camera_pose(start + frame)[0], ch.camera_pose(start)[0]))
        self.assertLess(first, 0.001)                      # no jump: it eases out of rest
        arrived = ch.camera_pose(start + 2.0 * timeline.BAR)
        self.assertEqual(arrived[0], layout.CAMERA_DISPOSAL_POSITION)
        self.assertEqual(arrived, ch.camera_pose(timeline.TIMELINE_END))
        for i in range(int(2.0 * timeline.BAR * timeline.FPS)):
            step = length(sub(ch.camera_pose(start + (i + 1) * frame)[0], ch.camera_pose(start + i * frame)[0]))
            self.assertLess(step, 0.06)


class LandfillTests(unittest.TestCase):
    """Below the floor: a cut, a fall, and an arrival among what was disposed of before."""

    def setUp(self):
        self.p, self.a = variants.primary(), variants.alternate()
        self.threshold = ch.disposal_threshold_time()

    def test_the_cut_follows_the_threshold_and_lands_on_fill(self):
        self.assertGreater(timeline.LANDFILL_CUT, self.threshold)
        self.assertLess(timeline.LANDFILL_CUT - self.threshold, 0.3)
        self.assertFalse(ch.camera_is_below(timeline.LANDFILL_CUT - 1.0 / timeline.FPS))
        self.assertTrue(ch.camera_is_below(timeline.LANDFILL_CUT))
        # A cut, not a move: the two cameras are nowhere near each other.
        self.assertGreater(length(sub(ch.camera_pose(timeline.LANDFILL_CUT)[0], ch.lower_camera_pose(timeline.LANDFILL_CUT)[0])), 5.0)

    def test_motion_is_continuous_through_the_threshold(self):
        # Position and speed of the forearm do not jump where carrying turns into falling.
        dt = 1e-4
        for v in (self.p, self.a):
            before = (ch.discard_position(v, self.threshold)[2] - ch.discard_position(v, self.threshold - dt)[2]) / dt
            after = (ch.discard_position(v, self.threshold + dt)[2] - ch.discard_position(v, self.threshold)[2]) / dt
            self.assertAlmostEqual(before, after, places=1)
            self.assertLess(before, -4.0)

    def test_the_fall_is_long_and_only_ever_downward(self):
        a = self.a
        fallen = ch.discard_position(a, self.threshold)[2] - ch.discard_position(a, timeline.LANDFILL_IMPACT)[2]
        self.assertGreater(fallen, 20.0)
        self.assertAlmostEqual(ch.discard_impact_time(a), timeline.LANDFILL_IMPACT)
        previous = ch.discard_position(a, self.threshold)[2]
        frames = int((timeline.LANDFILL_IMPACT - self.threshold) * timeline.FPS)
        for i in range(1, frames + 1):
            z = ch.discard_position(a, self.threshold + i / timeline.FPS)[2]
            self.assertLess(z, previous)
            previous = z

    def test_one_hop_then_rest(self):
        a, impact = self.a, timeline.LANDFILL_IMPACT
        landed = ch.discard_position(a, impact)[2]
        top = max(ch.discard_position(a, impact + i / 120.0)[2] for i in range(60))
        self.assertGreater(top - landed, 0.1)
        self.assertLess(top - landed, 0.3)
        self.assertEqual(ch.discard_position(a, impact + 0.5), ch.discard_position(a, timeline.TIMELINE_END))
        self.assertAlmostEqual(ch.discard_position(a, timeline.TIMELINE_END)[2], landed, places=6)
        # Nothing moves it afterwards.
        self.assertEqual(ch.detach_pose(a, impact + 1.0), ch.detach_pose(a, timeline.TIMELINE_END))

    def test_the_forearm_is_the_one_the_camera_keeps(self):
        from procedural_disagreement.core.vec import q_conj, q_rotate
        frames = int((timeline.LANDFILL_FLYOVER - timeline.LANDFILL_CUT) * timeline.FPS)
        for i in range(frames):
            t = timeline.LANDFILL_CUT + i / timeline.FPS
            position, rotation, fov = ch.lower_camera_pose(t)
            seen = q_rotate(q_conj(rotation), sub(ch.discard_position(self.a, t), position))
            half = math.tan(math.radians(fov * 0.5))
            self.assertLess(abs(seen[0] / -seen[2] / (half * 16.0 / 9.0)), 0.6, t)
            self.assertLess(abs(seen[1] / -seen[2] / half), 0.7, t)
        # The primary's arm ends well apart from it, and lower.
        apart = sub(ch.discard_landing(self.p), ch.discard_landing(self.a))
        self.assertGreater(length(apart), 2.5)
        self.assertLess(apart[2], -2.0)

    def test_the_lower_camera_never_jumps(self):
        previous = ch.lower_camera_pose(timeline.LANDFILL_CUT)[0]
        for i in range(1, int((timeline.TIMELINE_END - timeline.LANDFILL_CUT) * timeline.FPS)):
            now = ch.lower_camera_pose(timeline.LANDFILL_CUT + i / timeline.FPS)[0]
            self.assertLess(length(sub(now, previous)), 0.7)
            previous = now
        self.assertAlmostEqual(length(sub(ch.lower_camera_pose(timeline.LANDFILL_IMPACT + 0.3)[0], layout.LOWER_CAMERA_END)), 0.0)

    def test_loose_refuse_shifts_once_on_impact(self):
        self.assertEqual(ch.landfill_nudge(timeline.LANDFILL_IMPACT), 0.0)
        self.assertEqual(ch.landfill_nudge(timeline.LANDFILL_IMPACT + 0.3), 1.0)
        self.assertEqual(ch.landfill_nudge(timeline.TIMELINE_END), 1.0)


class FlyoverTests(unittest.TestCase):
    """After the landing the camera leaves: over the heap, across the field, climbing."""

    def setUp(self):
        self.start = timeline.LANDFILL_FLYOVER
        self.wide = timeline.LANDFILL_FLYOVER_WIDE

    def test_it_starts_after_the_forearm_has_settled_and_from_rest(self):
        a = variants.alternate()
        self.assertGreater(self.start, timeline.LANDFILL_IMPACT + 0.3)
        self.assertEqual(ch.lower_camera_pose(self.start), ch.lower_camera_pose(self.start - 0.03))
        frame = 1.0 / timeline.FPS
        first = length(sub(ch.lower_camera_pose(self.start + frame)[0], ch.lower_camera_pose(self.start)[0]))
        self.assertLess(first, 0.01)
        # The fall, the landing and the forearm itself are exactly as they were.
        self.assertAlmostEqual(length(sub(ch.discard_position(a, self.start), ch.discard_position(a, timeline.TIMELINE_END))), 0.0)

    def test_it_is_a_flight_forward_not_a_pullback(self):
        heading = ch.flyover_heading()
        previous = 0.0
        for i in range(1, int((timeline.TIMELINE_END - self.start) * timeline.FPS)):
            t = self.start + i / timeline.FPS
            flown = ch.flyover_distance(t)
            self.assertGreater(flown, previous)             # always forward
            self.assertLess(flown - previous, 0.3)          # never more than 9 m/s
            previous = flown
        moved = sub(ch.lower_camera_pose(self.wide)[0], ch.lower_camera_pose(self.start)[0])
        forward = moved[0] * heading[0] + moved[1] * heading[1]
        self.assertGreater(forward, 50.0)
        self.assertGreater(forward, 3.0 * moved[2])         # far more travel than climb
        self.assertEqual(ch.lower_camera_pose(self.start)[2], ch.lower_camera_pose(self.wide)[2])   # no zoom

    def test_it_glides_low_first_then_climbs(self):
        climb = timeline.LANDFILL_FLYOVER_CLIMB
        self.assertLess(ch.flyover_height(climb), 1.0)
        self.assertLess(ch.flyover_distance(climb), 4.0)
        self.assertAlmostEqual(ch.flyover_height(self.wide), 14.6)
        previous = 0.0
        for i in range(int((self.wide - self.start) * timeline.FPS)):
            h = ch.flyover_height(self.start + i / timeline.FPS)
            self.assertGreaterEqual(h, previous)
            previous = h

    def test_it_stays_inside_the_pit(self):
        position = ch.lower_camera_pose(timeline.TIMELINE_END)[0]
        landing = ch.discard_landing(variants.alternate())
        # ...and, at the end, still has most of the field in front of it.
        ahead = ch.flyover_heading()
        for k in (0, 1):
            centre = landing[k] + layout.LANDFILL_CENTRE_OFFSET[k]
            self.assertLess(abs(position[k] - centre), layout.LANDFILL_SPAN * 0.5 - 60.0)
            self.assertGreater(centre + layout.LANDFILL_SPAN * 0.5 - position[k], 100.0 * ahead[k])
        self.assertLess(position[2], -6.0)                  # under the chutes that hang from the ceiling

    def test_the_forearm_is_seen_at_the_start_and_then_left_behind(self):
        from procedural_disagreement.core.vec import q_conj, q_rotate
        landing = ch.discard_landing(variants.alternate())

        def in_frame(t):
            position, rotation, fov = ch.lower_camera_pose(t)
            seen = q_rotate(q_conj(rotation), sub(landing, position))
            half = math.tan(math.radians(fov * 0.5))
            return seen[2] < 0 and abs(seen[0] / -seen[2]) < half * 16.0 / 9.0 and abs(seen[1] / -seen[2]) < half

        self.assertTrue(in_frame(self.start))
        self.assertTrue(in_frame(self.start + 0.8))
        self.assertFalse(in_frame(timeline.LANDFILL_FLYOVER_CLIMB + 2.0))
        self.assertFalse(in_frame(self.wide))


class LandfillFieldTests(unittest.TestCase):
    """The disposal field: terrain, stations, and other disposals still going on."""

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.core import landfill
        cls.field = landfill
        cls.frame = landfill.frame()

    def seen(self, point, t):
        from procedural_disagreement.core.vec import q_conj, q_rotate
        position, rotation, fov = ch.lower_camera_pose(t)
        v = q_rotate(q_conj(rotation), sub(point, position))
        if v[2] >= 0:
            return None
        half = math.tan(math.radians(fov * 0.5))
        return v[0] / -v[2] / (half * 16.0 / 9.0), v[1] / -v[2] / half, -v[2]

    def test_terrain_is_deterministic_and_meets_the_landing(self):
        f, field = self.frame, self.field
        self.assertEqual(field.height(31.7, 12.3), field.height(31.7, 12.3))
        # The top of our heap is exactly under the platform the forearm lands on...
        self.assertAlmostEqual(field.surface(f["crest"][0], f["crest"][1]), f["crest"][2] - 0.2, places=6)
        # ...the lower platform stands clear of the waste...
        self.assertLessEqual(field.surface(f["shelf"][0], f["shelf"][1]), f["shelf"][2] - 0.3 + 1e-9)
        # ...and the forearm's own landing place is unchanged by any of this.
        self.assertAlmostEqual(ch.discard_landing(variants.alternate())[2], f["crest"][2] + 0.10, places=6)

    def test_terrain_is_benches_and_faces_not_mounds(self):
        field = self.field
        heights, steep = [], 0
        for i in range(60):
            for j in range(30):
                x, y = field.from_flight(-30.0 + i * 3.0, -45.0 + j * 3.0)
                heights.append(field.height(x, y))
                steep += field.steepness(x, y)[0] > 0.85
        # A good share of the ground sits near a bench level; some is steep face; some is basin.
        near_bench = sum(1 for h in heights if h > 0.3 and abs(h / field.BENCH - round(h / field.BENCH)) < 0.2)
        self.assertGreater(near_bench / len(heights), 0.35)
        self.assertGreater(steep, 60)
        self.assertGreater(sum(1 for h in heights if h < 0.3), 30)
        self.assertGreater(max(heights), 6.0)

    def test_the_camera_never_meets_the_ground(self):
        field = self.field
        for i in range(int((timeline.TIMELINE_END - timeline.LANDFILL_CUT) * 10)):
            position = ch.lower_camera_pose(timeline.LANDFILL_CUT + i / 10.0)[0]
            self.assertGreater(position[2] - field.surface(position[0], position[1]), 2.0)

    def test_there_are_stations_all_the_way_out(self):
        field, f = self.field, self.frame
        stations = field.stations()
        self.assertGreater(len(stations), 200)
        furthest = max(math.hypot(s.x - f["centre"][0], s.y - f["centre"][1]) for s in stations)
        self.assertGreater(furthest, layout.LANDFILL_SPAN * 0.5)
        for s in stations:
            self.assertGreater(math.hypot(s.x - f["crest"][0], s.y - f["crest"][1]), 18.0)
        # The field has gone dark long before its walls.
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            edge = (f["centre"][0] + dx * layout.LANDFILL_SPAN * 0.5, f["centre"][1] + dy * layout.LANDFILL_SPAN * 0.5)
            self.assertLess(field.shade(*edge), 0.01)
        self.assertGreater(field.shade(*field.from_flight(40.0, 0.0)), 0.95)

    def test_other_disposals_are_staggered_on_bar_lines_during_the_flyover(self):
        events = self.field.events()
        self.assertGreaterEqual(len(events), 3)
        releases = [e.release for e in events]
        self.assertEqual(releases, sorted(releases))
        for a, b in zip(releases, releases[1:]):
            self.assertGreaterEqual(b - a, timeline.BAR - 1e-9)
        for e in events:
            self.assertGreater(e.release, timeline.LANDFILL_FLYOVER)
            self.assertLessEqual(e.release, timeline.LANDFILL_FLYOVER_WIDE)
            bars = (e.release - timeline.DOWNBEAT) / timeline.BAR
            self.assertAlmostEqual(bars, round(bars), places=6)
        self.assertIn("arm", [e.kind for e in events])
        self.assertGreater(len({e.kind for e in events}), 1)

    def test_each_disposal_falls_from_its_chute_to_the_waste_and_stays(self):
        field = self.field
        for e in field.events():
            self.assertFalse(field.event_pose(e, e.release - 0.5)[2])
            fall = field.event_fall_time(e)
            self.assertGreater(e.bottom - field.event_rest_height(e), 8.0)       # a real drop
            previous = e.bottom
            for i in range(1, int(fall * 30)):
                z = field.event_pose(e, e.release + i / 30.0)[0][2]
                self.assertLess(z, previous)
                previous = z
            rest = field.event_pose(e, e.release + fall + 1.0)
            self.assertAlmostEqual(rest[0][2], field.event_rest_height(e))
            self.assertEqual(rest, field.event_pose(e, timeline.TIMELINE_END + 5.0))
            self.assertLess(field.event_impact_time(e), timeline.TIMELINE_END)

    def test_each_disposal_happens_in_front_of_the_camera(self):
        field = self.field
        for e in field.events():
            for dt in (0.1, field.event_fall_time(e) * 0.5):
                seen = self.seen(field.event_pose(e, e.release + dt)[0], e.release + dt)
                self.assertIsNotNone(seen, e.name)
                self.assertLess(abs(seen[0]), 0.9, e.name)
                self.assertLess(abs(seen[1]), 0.95, e.name)
            mouth = self.seen((e.x, e.y, e.bottom), e.release)
            self.assertLess(abs(mouth[0]), 0.9, e.name)
            self.assertLess(abs(mouth[1]), 0.95, e.name)

    def test_the_first_is_near_enough_to_read_and_the_last_falls_through_the_widest_view(self):
        field = self.field
        first, last = field.events()[0], field.events()[-1]
        mid = first.release + field.event_fall_time(first) * 0.5
        self.assertLess(self.seen(field.event_pose(first, mid)[0], mid)[2], 16.0)
        self.assertEqual(last.release, timeline.LANDFILL_FLYOVER_WIDE)
        self.assertGreater(field.event_impact_time(last), timeline.LANDFILL_FLYOVER_WIDE + 1.0)

    def test_another_arm_is_disposed_of_under_the_second_landfill(self):
        from procedural_disagreement.core.vec import dot, normalize, q_rotate
        field = self.field
        other = field.events()[2]
        fill = (96.9, 98.0)         # the first "-fill", as measured (docs/lyric_alignment.md)
        # Released inside the held "-fill" of the repeated couplet, ten seconds after the first.
        self.assertEqual(other.kind, "arm")
        self.assertEqual(other.release, 107.5)
        self.assertLess(fill[0] + 10.0, other.release)
        self.assertLess(other.release, fill[1] + 10.0)
        # It is a station that was already standing there, not one placed for the purpose...
        self.assertIn((other.x, other.y, other.bottom), [(s.x, s.y, s.bottom) for s in field.stations()])
        # ...near enough to be told for an arm at 360p (14 to 20 px for its 1.2 m), not nearer...
        focal = 180.0 / math.tan(math.radians(layout.LOWER_CAMERA_FOV * 0.5))
        fall = field.event_fall_time(other)
        for fraction in (0.25, 0.5, 0.75):
            t = other.release + fall * fraction
            position, rotation, _ = field.event_pose(other, t)
            depth = self.seen(position, t)[2]
            self.assertTrue(14.0 <= focal * 1.22 / depth <= 21.0, depth)
            # ...and its length lies across the line of sight for the whole fall.
            camera = ch.lower_camera_pose(t)[0]
            sight = normalize((position[0] - camera[0], position[1] - camera[1], 0.0))
            self.assertLess(abs(dot(q_rotate(rotation, (1.0, 0.0, 0.0)), sight)), 0.12)

    def test_moving_that_disposal_left_the_ground_as_it_was(self):
        # The basin and chute first staged for it are still there, idle.
        field = self.field
        site = field.staged_sites()[2]
        self.assertAlmostEqual(field.height(site.x, site.y), 1.2)
        self.assertEqual(len(field.staged_sites()), len(field.events()))

    def test_the_camera_follows_none_of_them(self):
        # Its path is a straight line in plan: nothing bends it toward a falling object.
        for i in range(0, 130):
            position = ch.lower_camera_pose(timeline.LANDFILL_FLYOVER + i / 10.0)[0]
            self.assertLess(abs(self.field.flight_coordinates(position[0], position[1])[1]), 1e-6)


class StableHashTests(unittest.TestCase):
    def test_range_and_repeatability(self):
        values = [stablehash.value(timeline.SEED, i) for i in range(2000)]
        self.assertTrue(all(0.0 <= v < 1.0 for v in values))
        self.assertEqual(values, [stablehash.value(timeline.SEED, i) for i in range(2000)])
        self.assertGreater(len(set(values)), 1900)

    def test_pinned_values(self):
        # If these change, every seeded placement in the video changes with them.
        self.assertAlmostEqual(stablehash.value(4401, 0), 0.38879430294036865)
        self.assertAlmostEqual(stablehash.value(4401, 1), 0.5079058408737183)


class ProfileIndependenceTests(unittest.TestCase):
    def test_shared_realities_are_identical(self):
        preview = variants.for_profile(profiles.PREVIEW)
        final = variants.for_profile(profiles.FINAL)
        self.assertEqual(preview, final[:len(preview)])
        # Final builds exactly the approved realities, no more (director, 2026-10-22).
        self.assertEqual(len(final), len(preview))

    def test_extra_alternates_do_not_depend_on_how_many_exist(self):
        self.assertEqual(variants.extra_alternate(2), variants.extra_alternate(2))
        self.assertNotEqual(variants.extra_alternate(1), variants.extra_alternate(2))

    def test_every_event_fits_inside_the_section(self):
        for v in variants.for_profile(profiles.FINAL):
            self.assertLess(v.cut_time + v.detach_duration, timeline.SECTION_END + 1e-6, v.name)
            self.assertLess(v.tower_fail_time + 4.5, timeline.SECTION_END, v.name)


class ChoreographyTests(unittest.TestCase):
    def test_camera_endpoints_and_purity(self):
        position, rotation, fov = ch.camera_pose(timeline.SECTION_START)
        self.assertEqual(position, layout.CAMERA_START)
        self.assertAlmostEqual(fov, layout.CAMERA_FOV_START)
        self.assertAlmostEqual(length(sub(ch.camera_pose(timeline.SECTION_END)[0], layout.CAMERA_END)), 0.0)
        self.assertEqual(ch.camera_pose(47.3), ch.camera_pose(47.3))
        self.assertAlmostEqual(sum(c * c for c in rotation), 1.0)

    def test_camera_never_jumps(self):
        previous = None
        for t in section_times(1.0 / timeline.FPS):
            position = ch.camera_pose(t)[0]
            if previous is not None:
                self.assertLess(length(sub(position, previous)), 0.06)
            previous = position

    def test_rotor_is_continuous_and_never_reverses(self):
        for v in (variants.primary(), variants.alternate()):
            fail = v.tower_fail_time
            previous = ch.rotor_angle(v, timeline.SECTION_START, fail)
            for t in section_times(0.01):
                angle = ch.rotor_angle(v, t, fail)
                self.assertGreaterEqual(angle, previous - 1e-9)
                self.assertLess(angle - previous, 1.3)  # 96 deg/s * 0.01 s, with margin
                previous = angle

    def test_primary_rotor_stops_and_alternate_keeps_turning(self):
        p, a = variants.primary(), variants.alternate()
        late = timeline.SECTION_END
        self.assertAlmostEqual(ch.rotor_angle(p, late, p.tower_fail_time), ch.rotor_angle(p, late - 1.0, p.tower_fail_time))
        self.assertGreater(ch.rotor_angle(a, late, a.tower_fail_time), ch.rotor_angle(a, late - 1.0, a.tower_fail_time) + 10.0)

    def test_intact_dependency_never_fails(self):
        v = variants.primary()
        for t in section_times(0.5):
            self.assertGreater(ch.conduit_energy(0.5, t, ch.NEVER, v.signal_travel), 0.2)
            self.assertAlmostEqual(ch.rotor_angle(v, t, ch.NEVER), 60.0 / timeline.BEAT * t)
            self.assertGreater(ch.cell_energy(v, 0, t, ch.NEVER, 1), 0.5)

    def test_darkness_travels_from_body_to_tower(self):
        v = variants.primary()
        midway = v.cut_time + v.signal_travel * 0.5
        self.assertAlmostEqual(ch.conduit_energy(0.1, midway, v.cut_time, v.signal_travel), 0.0)
        self.assertGreater(ch.conduit_energy(0.9, midway, v.cut_time, v.signal_travel), 0.2)
        after = v.cut_time + v.signal_travel
        for u in (0.0, 0.5, 1.0):
            self.assertAlmostEqual(ch.conduit_energy(u, after, v.cut_time, v.signal_travel), 0.0)

    def test_region_is_attached_until_its_cut(self):
        for v in variants.for_profile(profiles.FINAL):
            offset, rotation = ch.detach_pose(v, v.cut_time)
            self.assertAlmostEqual(length(offset), 0.0)
            self.assertEqual(rotation, (1.0, 0.0, 0.0, 0.0))
            self.assertGreater(length(ch.detach_pose(v, v.cut_time + v.detach_duration)[0]), 0.5)

    def test_plane_sits_on_its_own_cut_when_it_cuts(self):
        p, a = variants.primary(), variants.alternate()
        for cue, owner, rival in ((ch.PLANE_A, p, a), (ch.PLANE_B, a, p)):
            position, rotation, scale, opacity = ch.plane_pose(cue, owner, rival, owner.cut_time)
            self.assertAlmostEqual(length(sub(position, ch.cut_point(owner, owner.cut_time))), 0.0)
            self.assertGreater(opacity, 1.0)  # the flash
            self.assertAlmostEqual(ch.plane_pose(cue, owner, rival, timeline.SECTION_START)[3], 0.0)

    def test_the_two_cuts_disagree(self):
        p, a = variants.primary(), variants.alternate()
        self.assertNotEqual(p.cut_index, a.cut_index)
        self.assertNotEqual(p.cut_time, a.cut_time)
        gap = length(sub(ch.cut_point(p, timeline.SECTION_END), ch.cut_point(a, timeline.SECTION_END)))
        self.assertGreater(gap, 0.3)

    def test_alternates_start_coincident_and_hidden(self):
        a = variants.alternate()
        self.assertEqual(ch.presence(a, timeline.SECTION_START), 0.0)
        self.assertEqual(ch.reality_offset(a, timeline.SECTION_START), (0.0, 0.0, 0.0))
        self.assertEqual(ch.presence(a, timeline.DIVERGENCE_END), 1.0)

    def test_stutter_does_not_depend_on_frame_rate(self):
        v = variants.primary()
        fail = v.tower_fail_time
        t = fail + 0.2  # inside the top cell's stutter window
        self.assertEqual(ch.cell_energy(v, 0, t, fail, 7), ch.cell_energy(v, 0, t, fail, 7))
        self.assertTrue(math.isfinite(ch.cell_energy(v, 0, t, fail, 7)))


class LyricTests(unittest.TestCase):
    """The sung lyric in Chinese: the final translation, when each line is shown, and where."""

    @classmethod
    def setUpClass(cls):
        from procedural_disagreement.presentation import glyphs, lyrics, screens
        cls.glyphs, cls.lyrics, cls.screens = glyphs, lyrics, screens

    def test_the_translation_is_the_final_one_word_for_word(self):
        self.assertEqual(self.lyrics.TEXT, {
            "A1": "捨棄那冒犯性的軀幹", "A2": "卻將它封聖於殘肢", "B1": "我寧願它從未存在",
            "B2": "也想知道它在哪座垃圾掩埋場", "C1": "這些潦草的土地致謝聲明", "C2": "這些強人胸前的勳表"})
        for key, groups in self.lyrics.GROUPS.items():
            self.assertEqual("".join("".join(half) for half in groups), self.lyrics.TEXT[key], key)

    def test_every_statement_is_shown_from_its_first_syllable_and_never_two_at_once(self):
        windows = self.lyrics.windows()
        for name, start, end in self.lyrics.SUNG:
            mine = [w for w in windows if w[1] == name and w[2] < end and w[3] > start]
            self.assertTrue(mine, (name, start))
            self.assertAlmostEqual(min(w[2] for w in mine), start)
            self.assertGreaterEqual(max(w[3] for w in mine), end)
        spans = sorted((w[2], w[3]) for w in windows)
        for (_, a), (b, _) in zip(spans, spans[1:]):
            self.assertLessEqual(a, b + 1e-9)

    def test_a_line_sung_across_a_cut_is_shown_in_two_parts(self):
        for key, _, start, end in self.lyrics.windows():
            for cut in self.lyrics.CUTS:
                self.assertFalse(start < cut < end, (key, cut))
        self.assertIn("B2@94.85/1", [w[0] for w in self.lyrics.windows()])

    def test_every_character_has_a_unifont_glyph(self):
        text = "".join(self.lyrics.TEXT.values())
        for character in set(text):
            glyph = self.glyphs.glyph(character, text)
            self.assertEqual(len(glyph), 16)
            self.assertEqual(len(glyph[0]), 16, character)
            self.assertTrue(any(any(row) for row in glyph), character)

    def test_packing_keeps_phrases_whole_and_in_reading_order(self):
        pack, groups = self.lyrics.pack, self.lyrics.GROUPS
        self.assertEqual(pack(groups["B2"], [5, 5, 5], 1), ["也想知道", "它在哪座", "垃圾掩埋場"])
        self.assertIsNone(pack(groups["B2"], [3, 3], 1))
        # Between the halves of a line before inside them: not "這些潦草的土地 / 致謝聲明".
        self.assertEqual(pack(groups["C1"], [8, 8, 8], 1), ["這些潦草的", "土地致謝聲明"])
        self.assertEqual(pack(groups["C2"], [8, 8, 8], 1), ["這些強人", "胸前的勳表"])
        for key, groups in self.lyrics.GROUPS.items():
            for rows, per in (([5, 5, 5], 1), ([3, 3, 3], 2), ([2, 4], 2), ([4, 4, 4], 1)):
                packed = self.lyrics.pack(groups, rows, per)
                if packed is not None:
                    self.assertEqual("".join(packed), self.lyrics.TEXT[key])
                    for text, cells in zip(packed, rows):
                        self.assertLessEqual(len(text), cells * per)

    def test_the_layout_shows_every_line_in_full_in_one_way(self):
        data = self.lyrics.layout()
        if data is None:
            self.skipTest("no layout yet: run tools/lyric_layout.py")
        self.assertEqual({e["key"] for e in data["windows"]}, {w[0] for w in self.lyrics.windows()})
        for e in data["windows"]:
            self.assertIn(e["mode"], ("crt", "world"))
            if e["mode"] == "crt":
                reading = sorted(e["cells"], key=lambda c: (-c[0], c[1]))
                self.assertEqual("".join(c[2] for c in reading), self.lyrics.TEXT[e["line"]], e["key"])
                self.assertEqual(len({(c[0], c[1]) for c in e["cells"]}), len(e["cells"]))
                for row, col, text in e["cells"]:
                    self.assertTrue(0 <= row < 3 and 0 <= col < 5)
                    self.assertTrue(1 <= len(text) <= (2 if e["scale"] == 2 else 4))
                    # The part of the glass that many characters occupy was measured readable.
                    region = str(max(e["per_screen"], len(text)))
                    self.assertTrue(e["screens"]["%d,%d" % (row, col)]["share"][region] >= 0.85, (e["key"], row, col))
            else:
                self.assertEqual("".join(e["world"]["rows"]), self.lyrics.TEXT[e["line"]], e["key"])
                shown = e["world"]["shown"]
                self.assertTrue(e["start"] <= shown[0] < shown[1] <= e["end"], e["key"])

    def test_no_word_is_split_across_two_screens(self):
        for e in self.lyrics.crt_lines():
            ends, position = set(), 0
            for word in self.lyrics.WORDS[e["line"]]:
                position += len(word)
                ends.add(position)
            position = 0
            for cell in sorted(e["cells"], key=lambda c: (-c[0], c[1])):
                position += len(cell[2])
                self.assertIn(position, ends, (e["key"], cell))
        coda = [e for e in self.lyrics.crt_lines() if e["key"] == "C1@255.10"]
        if coda:
            self.assertIn(["土地", "致謝聲明"], [[c[2] for c in coda[0]["cells"] if c[0] == 0]])

    def test_no_line_is_put_up_after_it_has_been_sung(self):
        data = self.lyrics.layout()
        if data is None:
            self.skipTest("no layout yet")
        for e in data["windows"]:
            first, last = self.lyrics.sung(e["key"])
            shown = e["world"]["shown"] if e["mode"] == "world" else [e["start"], e["end"]]
            self.assertGreaterEqual(shown[0], e["start"] - 1e-6, e["key"])
            self.assertLessEqual(shown[1], e["end"] + 1e-6, e["key"])
            self.assertLessEqual(shown[0], last - 1.0, e["key"])
            if "/" not in e["key"]:
                # Only the part of a line after a cut may wait for its place.
                self.assertAlmostEqual(shown[0], first, places=3, msg=e["key"])

    def test_the_canvas_is_hard_pixels_inside_the_screens_that_carry_text(self):
        for e in self.lyrics.crt_lines():
            pixels = self.lyrics.canvas(e)
            self.assertLessEqual(set(pixels), {0, 1})
            lit = {(i % 320 // 64, 2 - i // 320 // 48) for i, v in enumerate(pixels) if v}
            self.assertEqual(lit, {(c[1], c[0]) for c in e["cells"]}, e["key"])

    def test_from_4_15_only_the_screens_with_words_are_on(self):
        on = 0
        for frame in range(timeline.frame_of(outer.CODA_START), timeline.frame_of(outer.ENDING_END)):
            t = timeline.time_of(frame)
            cells = self.lyrics.crt_cells(t)
            for row in range(3):
                for col in range(5):
                    self.assertEqual(self.screens.wake(row, col, t), 1.0 if (row, col) in cells else 0.0)
            on += bool(cells)
        if self.lyrics.layout() is not None:
            self.assertGreater(on, 0)
            self.assertEqual(self.lyrics.crt_cells(outer.ENDING_START + 0.5), set())

    def test_footage_is_shown_only_where_there_is_some(self):
        if self.screens.video_frames() is None:
            for t in (61.0, 70.0, 85.0):
                self.assertEqual(self.screens.video(t), 0.0)
        self.assertEqual(self.screens.video(30.0), 0.0)
        self.assertEqual(self.screens.video(256.0), 0.0)


if __name__ == "__main__":
    unittest.main()
