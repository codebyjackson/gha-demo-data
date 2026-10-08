"""Email the team after the agent has looked at a failed Build data run.

Reads everything from environment variables set in claude-fix.yml. If the SMTP
settings aren't there yet, it prints the email to the log instead of sending it.
"""
import json
import os
import re
import smtplib
import ssl
import subprocess
from email.message import EmailMessage

env = os.environ.get
SITE_URL = "https://codebyjackson.github.io/gha-demo-site/"


def find_pr(branch):
    """The PR the agent opened from its fix branch, or None."""
    try:
        out = subprocess.run(
            ["gh", "pr", "list", "--head", branch, "--state", "all", "--limit", "1",
             "--json", "number,url,title,body"],
            capture_output=True, text=True, check=True).stdout
        prs = json.loads(out or "[]")
        return prs[0] if prs else None
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return None


def claude_verdict(path):
    """Claude's final message from the action's execution log, if there is one."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for msg in reversed(data if isinstance(data, list) else [data]):
            if msg.get("type") == "result" and msg.get("result"):
                return msg["result"].strip()
    except (OSError, TypeError, ValueError, AttributeError):
        pass
    return ""


def error_lines(log):
    """The lines of the failed log that explain the error, in plain words."""
    lines = []
    for line in log.splitlines():
        text = line.split("\t")[-1].strip()                       # drop "job<TAB>step<TAB>"
        text = re.sub(r"^\d{4}-\d{2}-\d{2}T[\d:.]+Z\s*", "", text)  # drop the timestamp
        text = re.sub(r"^::error file=([^,]+),line=(\d+)::", r"\1 line \2: ", text)
        text = text.replace("##[error]", "Error: ")
        lines.append(text)
    picked = [l for l in lines if "error" in l.lower()]
    return "\n".join("  " + l for l in (picked or lines)[-8:])


def build_email():
    commit = env("COMMIT", "")[:7]
    author = env("AUTHOR", "someone")
    message = (env("COMMIT_MSG", "") or "").splitlines()[0] if env("COMMIT_MSG") else ""
    pr = find_pr(env("BRANCH", ""))
    said = claude_verdict(env("CLAUDE_OUTPUT", ""))

    if pr:
        subject = f"[gha-demo] Claude fixed it: PR #{pr['number']} is ready for you to merge"
        verdict = (f"Claude found the problem and fixed it on a branch. Nothing is live until you merge.\n"
                   f"Review and merge: {pr['url']}\n\n"
                   f"The fix: {pr['title']}\n{'-' * (9 + len(pr['title']))}\n{pr['body'].strip()}")
    elif said:
        subject = "[gha-demo] Claude needs your decision: Build data failed"
        verdict = f"Claude did not change anything. It needs you to choose the fix. In its words:\n\n{said}"
    else:
        subject = "[gha-demo] Build data failed and needs a human"
        verdict = "Claude did not open a fix and gave no explanation. The agent run may have failed; open it below."

    # Also show the verdict on the agent run's summary page
    summary = env("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(f"## What Claude decided\n\n{verdict}\n")

    body = f"""Build data failed on main, so the site was not updated. It still shows the last good data.

What was pushed:  {commit} by {author}  "{message}"
What went wrong:
{error_lines(env("FAILED_LOG", ""))}

{verdict}

Failed run:  {env("RUN_URL", "")}
Agent run:   {env("AGENT_RUN_URL", "")}
Live site:   {SITE_URL}
"""
    return subject, body


def main():
    subject, body = build_email()
    to = [a.strip() for a in (env("EMAIL_TO") or "").split(",") if a.strip()]
    server, user, password = env("SMTP_SERVER"), env("SMTP_USERNAME"), env("SMTP_PASSWORD")

    if not (to and server and user and password):
        print("::notice::Email is not set up yet (SMTP secrets or NOTIFY_EMAIL_TO missing). This is what would be sent:")
        print(f"Subject: {subject}\n\n{body}")
        return

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = env("EMAIL_FROM") or user
    msg["To"] = ", ".join(to)
    msg.set_content(body)

    port = int(env("SMTP_PORT") or 465)
    context = ssl.create_default_context()
    if port == 465:
        with smtplib.SMTP_SSL(server, port, context=context, timeout=30) as smtp:
            smtp.login(user, password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(server, port, timeout=30) as smtp:
            smtp.starttls(context=context)
            smtp.login(user, password)
            smtp.send_message(msg)
    print(f"Emailed {len(to)} recipient(s): {subject}")


if __name__ == "__main__":
    main()
