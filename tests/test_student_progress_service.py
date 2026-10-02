from decimal import Decimal

from app.services.student_progress_service import StudentProgressService


def test_roadmap_shows_current_progress_and_milestone_states():
    progress = StudentProgressService().build_roadmap(Decimal("12.5"))

    assert progress.current_hours == Decimal("12.5")
    assert progress.next_milestone is not None
    assert progress.next_milestone.name == "Milestone 2"
    assert progress.next_milestone.progress_percent == 56
    assert progress.hours_to_next == Decimal("3.5")
    assert [milestone.achieved for milestone in progress.milestones] == [
        True,
        False,
        False,
        False,
    ]


def test_roadmap_marks_all_milestones_achieved_at_final_threshold():
    progress = StudentProgressService().build_roadmap(Decimal("32"))

    assert progress.next_milestone is None
    assert progress.hours_to_next == Decimal("0")
    assert all(milestone.achieved for milestone in progress.milestones)