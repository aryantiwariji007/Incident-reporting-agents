import json
from pathlib import Path
from crewai import Crew
from tasks import research_task, analysis_task, report_task

OUTPUT_FILE = Path(__file__).parent / "ai_incidents_report.json"


def run_pipeline():
    """Run the Crew pipeline: Researcher → Analyst → Reporter."""
    crew = Crew(tasks=[research_task, analysis_task, report_task],verbose=True)

    print("🚀 Launching Crew with kickoff() ...")
    result = crew.kickoff()

    if not result or (hasattr(result, "reports") and getattr(result, "reports") in (None, [], {})):
        return None
    return result


if __name__ == "__main__":
    try:
        final_report = run_pipeline()

        if final_report is None:
            print(f"⚠️  No recent harmful AI incidents found (within {MAX_AGE_DAYS} days).")
        else:
            # Serialize to JSON
            if hasattr(final_report, "model_dump_json"):
                json_text = final_report.model_dump_json(indent=2)
            elif hasattr(final_report, "json"):
                json_text = final_report.json(indent=2)
            else:
                json_text = json.dumps(final_report, indent=2)

            OUTPUT_FILE.write_text(json_text, encoding="utf-8")
            print(f"✅ Report saved to {OUTPUT_FILE.resolve()}")

    except Exception as exc:
        print("❌ Error while running pipeline:", exc)
