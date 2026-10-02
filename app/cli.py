#!/usr/bin/env python3
"""FastStarter project CLI — stdlib argparse (no extra CLI library).

From the project root (venv active, deps installed; ``.env`` optional — falls back to ``.env.example``):

    python manage.py init
    python manage.py run
    python manage.py users
    python manage.py report --name "Student Name" --id "816000000"
    python manage.py usecase
    python manage.py skills-verify
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_models_loaded() -> None:
    import app.models  # noqa: F401


def cmd_init(args: argparse.Namespace) -> None:
    """Create database tables (drops existing by default) and seed demo users."""
    from app.config import get_settings
    from app.database import drop_all, ensure_db_and_tables

    _ensure_models_loaded()
    if args.drop:
        print("Dropping all tables…")
        # Drop can fail on a brand-new empty DB; create path still retries.
        try:
            drop_all()
        except Exception as exc:  # noqa: BLE001
            from app.database import is_db_not_ready_error

            if not is_db_not_ready_error(exc):
                raise
            print(f"Database not ready yet while dropping ({exc}); continuing…")
    print("Creating tables…")
    ensure_db_and_tables()
    print(f"Database ready ({get_settings().database_uri}).")
    if getattr(args, "seed", True):
        cmd_seed(args)


def cmd_seed(args: argparse.Namespace) -> None:
    """Insert demo users.

    bob / bobpass       (regular_user)
    alice / alicepass   (regular_user)
    chris / chrispass   (regular_user)
    dana / danapass     (regular_user)
    admin / adminpass   (admin)
    """
    from datetime import date, timedelta
    from decimal import Decimal

    from app.database import ensure_db_and_tables, get_cli_session
    from app.repositories.admin import AdminRepository
    from app.repositories.opportunity import VolunteerOpportunityRepository
    from app.repositories.student import StudentRepository
    from app.repositories.user import UserRepository
    from app.models.volunteer_opportunity import VolunteerOpportunity
    from app.schemas.user import AdminCreate, RegularUserCreate
    from app.utilities.security import encrypt_password

    _ensure_models_loaded()
    ensure_db_and_tables()

    demo_users = [
        ("bob", "bob@example.com", "bobpass", "regular_user", "Class 1", Decimal("0")),
        ("alice", "alice@example.com", "alicepass", "regular_user", "Class 1", Decimal("0")),
        ("chris", "chris@example.com", "chrispass", "regular_user", "Class 2", Decimal("0")),
        ("dana", "dana@example.com", "danapass", "regular_user", "Class 2", Decimal("0")),
        ("admin", "admin@example.com", "adminpass", "admin", None, None),
    ]

    created = 0
    skipped = 0
    with get_cli_session() as session:
        repo = UserRepository(session)
        student_repo = StudentRepository(session)
        admin_repo = AdminRepository(session)
        opportunity_repo = VolunteerOpportunityRepository(session)
        for username, email, password, role, class_name, seed_hours in demo_users:
            user = repo.get_by_username(username)
            if user:
                if role == "admin":
                    admin_repo.ensure_for_user(user)
                else:
                    student = student_repo.ensure_for_user(user, class_name=class_name)
                    if student.class_name != class_name:
                        student.class_name = class_name
                        session.add(student)
                        session.commit()
                print(f"  skip  {username} (already exists)")
                skipped += 1
                continue
            payload_cls = AdminCreate if role == "admin" else RegularUserCreate
            user = repo.create(
                payload_cls(
                    username=username,
                    email=email,
                    password=encrypt_password(password),
                    role=role,
                )
            )
            if role == "admin":
                admin_repo.ensure_for_user(user)
            else:
                student = student_repo.ensure_for_user(user, class_name=class_name)
                student.hours = seed_hours
                session.add(student)
                session.commit()
            print(f"  create {username} ({role})")
            created += 1

        opportunities = opportunity_repo.list_all()
        if not opportunities:
            start = date.today() + timedelta(days=7)
            opportunities = [
                VolunteerOpportunity(
                    name="Campus Welcome Crew",
                    description="Help new students find campus services and settle into the first week.",
                    start_date=start,
                    end_date=start + timedelta(days=2),
                    max_applicants=12,
                    image_url="https://images.unsplash.com/photo-1531206715517-5c0ba140b2b8?auto=format&fit=crop&w=1000&q=85",
                ),
                VolunteerOpportunity(
                    name="Community Garden Day",
                    description="Work with fellow students to prepare planting beds and care for the campus garden.",
                    start_date=start + timedelta(days=7),
                    end_date=start + timedelta(days=7),
                    max_applicants=10,
                    image_url="https://images.unsplash.com/photo-1559027615-cd4628902d4a?auto=format&fit=crop&w=1000&q=85",
                ),
                VolunteerOpportunity(
                    name="Library Reading Circle",
                    description="Support a welcoming reading session for young learners in the community.",
                    start_date=start + timedelta(days=14),
                    end_date=start + timedelta(days=14),
                    max_applicants=8,
                    image_url="https://images.unsplash.com/photo-1509099836639-18ba1795216d?auto=format&fit=crop&w=1000&q=85",
                ),
                VolunteerOpportunity(
                    name="Food Bank Sorting Team",
                    description="Sort donated groceries and prepare food parcels for local families.",
                    start_date=start + timedelta(days=21),
                    end_date=start + timedelta(days=21),
                    max_applicants=14,
                    image_url="https://images.unsplash.com/photo-1593113598332-cd288d649433?auto=format&fit=crop&w=1000&q=85",
                ),
                VolunteerOpportunity(
                    name="Campus Clean-Up",
                    description="Help keep shared campus spaces clean, safe, and welcoming.",
                    start_date=start + timedelta(days=28),
                    end_date=start + timedelta(days=28),
                    max_applicants=20,
                    image_url="https://images.unsplash.com/photo-1532996122724-e3c354a0b15b?auto=format&fit=crop&w=1000&q=85",
                ),
                VolunteerOpportunity(
                    name="Digital Skills Mentors",
                    description="Assist community members as they practise everyday computer and internet skills.",
                    start_date=start + timedelta(days=35),
                    end_date=start + timedelta(days=35),
                    max_applicants=6,
                    image_url="https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=1000&q=85",
                ),
            ]
            opportunities = [opportunity_repo.create(item) for item in opportunities]
            print(f"  create {len(opportunities)} volunteer opportunities")

    print(f"Seed done — created {created}, skipped {skipped}.")
    print("Student logins: bob/bobpass, alice/alicepass, chris/chrispass, dana/danapass")
    print("Admin login: admin/adminpass")


def cmd_run(args: argparse.Namespace) -> None:
    """Start the FastAPI app with Uvicorn."""
    import uvicorn

    from app.config import get_settings

    settings = get_settings()
    bind_host = args.host or settings.app_host
    bind_port = args.port or settings.app_port
    if args.reload is None:
        use_reload = settings.env.lower() != "production"
    else:
        use_reload = args.reload
    print(f"Starting FastStarter on http://{bind_host}:{bind_port} (reload={use_reload})")
    uvicorn.run(
        "app.main:app",
        host=bind_host,
        port=bind_port,
        reload=use_reload,
    )


def cmd_report(args: argparse.Namespace) -> None:
    """Build the submission package: merge judge, package transcripts, write PDF.

    Guide must (1) write ``docs/judge.md`` and (2) pull every Guide chat into
    ``docs/transcripts/*.md`` before this command. Report only packages those files.
    """
    from app.report_pdf import export_report
    from app.skill_integrity import format_report, verify

    result = export_report(
        name=args.name,
        student_id=args.student_id,
        source=None if args.src is None else Path(args.src),
        output=None if args.output is None else Path(args.output),
    )
    print()
    print("Report package:")
    print(
        f"  Judge:       {'merged docs/judge.md' if result.judge_merged else 'MISSING - Guide must run student-judge first'}"
    )
    print(
        f"  Transcripts: {result.transcript_count} chat(s) in docs/transcripts/"
        + (
            ""
            if result.transcript_count
            else " (EMPTY - Guide must pull Copilot/Cursor/OpenCode chats first)"
        )
    )
    if result.transcript_zip:
        print(f"  Zip:         {result.transcript_zip.as_posix()}")
    print(f"  PDF:         {result.pdf_path.as_posix()}")
    print(format_report(verify()))


def cmd_transcripts(args: argparse.Namespace) -> None:
    """Package agent-written markdown under docs/transcripts/ (+ zip)."""
    from app.transcript_export import package_transcripts

    result = package_transcripts(make_zip=not args.no_zip)
    if result.found == 0:
        print(
            "Warning: no chat markdown in docs/transcripts/. "
            "The Guide agent must pull every Guide chat for this project "
            "(Copilot Agent, Cursor, or OpenCode) into docs/transcripts/<slug>.md first."
        )
        raise SystemExit(2)
    print(f"Submission package ready: {result.out_dir}")
    if result.zip_path:
        print(f"Zip for submission: {result.zip_path}")


def cmd_skills_verify(args: argparse.Namespace) -> None:
    """Check course skill files against .agents/skills.lock.json."""
    from app.skill_integrity import format_report, verify

    result = verify()
    print(format_report(result))
    if not result.ok:
        raise SystemExit(1)


def cmd_usecase(args: argparse.Namespace) -> None:
    """Render docs/diagrams/use-case.json to a UML use-case PNG."""
    from app.usecase_diagram import render_usecase_png

    dest = render_usecase_png(
        spec_path=None if args.spec is None else Path(args.spec),
        output=None if args.output is None else Path(args.output),
    )
    print(f"Wrote {dest}")


def cmd_skills_lock(args: argparse.Namespace) -> None:
    """Rewrite the skill lockfile (course authors only)."""
    from app.skill_integrity import write_lock

    dest = write_lock()
    print(f"Wrote {dest}")


def cmd_users(args: argparse.Namespace) -> None:
    """List users currently in the database."""
    from sqlmodel import select

    from app.database import get_cli_session
    from app.models.user import User

    _ensure_models_loaded()
    with get_cli_session() as session:
        users = session.exec(select(User)).all()
        if not users:
            print("No users found. Run: python manage.py init")
            return
        for user in users:
            print(
                f"  id={user.id}  username={user.username}  "
                f"role={user.role}  email={user.email}"
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python manage.py",
        description="FastStarter Python CLI — init database, seed demo data, run the app.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser(
        "init",
        help="Create DB tables and seed demo users (drops existing tables by default)",
    )
    p_init.add_argument(
        "--no-drop",
        dest="drop",
        action="store_false",
        help="Create tables without dropping existing ones",
    )
    p_init.add_argument(
        "--no-seed",
        dest="seed",
        action="store_false",
        help="Skip demo user seed after creating tables",
    )
    p_init.set_defaults(drop=True, seed=True, func=cmd_init)

    p_seed = sub.add_parser(
        "seed",
        help="Insert demo users only (idempotent; also runs as part of init)",
    )
    p_seed.set_defaults(func=cmd_seed)

    p_run = sub.add_parser("run", help="Start the web app (uvicorn)")
    p_run.add_argument("--host", default=None, help="Bind host")
    p_run.add_argument("--port", type=int, default=None, help="Bind port")
    reload_group = p_run.add_mutually_exclusive_group()
    reload_group.add_argument(
        "--reload", dest="reload", action="store_true", default=None, help="Enable auto-reload"
    )
    reload_group.add_argument(
        "--no-reload", dest="reload", action="store_false", help="Disable auto-reload"
    )
    p_run.set_defaults(func=cmd_run, reload=None)

    p_users = sub.add_parser("users", help="List users in the database")
    p_users.set_defaults(func=cmd_users)

    p_report = sub.add_parser(
        "report",
        help=(
            "Build submission package: merge docs/judge.md, package docs/transcripts/, "
            "write docs/report.pdf (Guide pulls chats + runs student-judge first)"
        ),
    )
    p_report.add_argument("--name", required=True, help="Student name (printed on the PDF cover)")
    p_report.add_argument("--id", dest="student_id", required=True, help="Student ID (PDF only)")
    p_report.add_argument("--src", default=None, help="Markdown path (default: docs/report.md)")
    p_report.add_argument("--output", default=None, help="PDF path (default: docs/report.pdf)")
    p_report.set_defaults(func=cmd_report)

    p_transcripts = sub.add_parser(
        "transcripts",
        help="Package agent-written docs/transcripts/*.md into INDEX + zip (no IDE scrape)",
    )
    p_transcripts.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip writing docs/transcripts.zip",
    )
    p_transcripts.set_defaults(func=cmd_transcripts)

    p_usecase = sub.add_parser(
        "usecase",
        help="Render docs/diagrams/use-case.json to a UML use-case PNG",
    )
    p_usecase.add_argument("--spec", default=None, help="JSON spec (default: docs/diagrams/use-case.json)")
    p_usecase.add_argument("--output", default=None, help="PNG path (default: docs/diagrams/use-case.png)")
    p_usecase.set_defaults(func=cmd_usecase)

    p_skills_verify = sub.add_parser(
        "skills-verify",
        help="Check course skills against .agents/skills.lock.json",
    )
    p_skills_verify.set_defaults(func=cmd_skills_verify)

    p_skills_lock = sub.add_parser(
        "skills-lock",
        help="Rewrite .agents/skills.lock.json (course authors; needs FASTSTARTER_SKILLS_LOCK=1)",
    )
    p_skills_lock.set_defaults(func=cmd_skills_lock)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
