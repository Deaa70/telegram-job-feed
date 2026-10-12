"""Application settings. Secrets come from environment variables (.env)."""
import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# -----------------------------------------------------------------------------
# Telegram channels / groups to read.
# The spare Telegram account must already be a member of each channel.
# Public channels use "@username"; private channels use their numeric ID.
# -----------------------------------------------------------------------------
CHANNELS = [
    "@forsa021",
    "@damasjob",
    "@higher_steps",
    "@Adamplatform",
    "@teleworksjobs",
    "@ShofeForas",
    "@syrianjobs2",
    "@hopeAleppo",
    "@JobsvacanciesinSyriaandTurkey",
    "@job_idleb",
    "@SyMOAD",
    "@KhotwaInsideSyria",
    "@ExtraJobs",
    "@remotejobshg",
    "@amalw3amal1",
    "@arabonlinework",
    "@OPENVACANCIES2022",
    "@Syrian_jobb",
    "@A_H_M_DY",
    "@technomajed",
    "@itcjobs",
    "@jobsintr",
    "@jops2015",
    "@jodfreelancer",
    "@jobs963",
    "@saudia_jobs",
    "@handasiah",
    "@Ksa_Reg",
    "@h_techno_learn",
    "@SWQJobsEG",
    "@ZAD_Jobs",
    "@tmhrjobs",
    "@PlatformSyria",
    "@workonline_saziz",
    "@extraActive",
    "@MGLNaJ",
    "@forsah0",
    "@jobsonlineSA",
    "@profinder_sy",
    "@RemoteOnlineWork",
    "@BAAB_CEN",
    "@cchellowork",
    "@syrianpower",
    "@freelancer_syria_jobs",
]

# -----------------------------------------------------------------------------
# Fetch settings (converted from the YAML `fetch` section).
# Values can be overridden using matching environment variables.
# -----------------------------------------------------------------------------
FIRST_RUN_LIMIT = int(os.getenv("FIRST_RUN_LIMIT", "50"))
MAX_PER_CHANNEL = int(os.getenv("MAX_PER_CHANNEL", "500"))
MAX_AGE_DAYS = int(os.getenv("MAX_AGE_DAYS", "7"))
MIN_CHARS = int(os.getenv("MIN_CHARS", "40"))

# Compatibility with the previous settings.py version. This assumes the reader's
# lookback window should match the maximum job age.
LOOKBACK_HOURS = int(os.getenv("LOOKBACK_HOURS", str(MAX_AGE_DAYS * 24)))

# -----------------------------------------------------------------------------
# LLM settings (converted from the YAML `llm` section).
# -----------------------------------------------------------------------------
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "20"))
MAX_BATCH_CHARS = int(os.getenv("MAX_BATCH_CHARS", "12000"))
MAX_CHARS_PER_MESSAGE = int(os.getenv("MAX_CHARS_PER_MESSAGE", "1500"))
MIN_SCORE = int(os.getenv("MIN_SCORE", "1"))

# Compatibility with the previous settings.py name.
MAX_CHARS_PER_POST = MAX_CHARS_PER_MESSAGE

# -----------------------------------------------------------------------------
# Schedule settings (used by --loop / the Docker container).
# -----------------------------------------------------------------------------
RUN_EVERY_HOURS = int(os.getenv("RUN_EVERY_HOURS", "8"))

# -----------------------------------------------------------------------------
# Telegram notification settings (converted from the YAML `notify` section).
# Arabic is selected intentionally; the previous YAML value `en` would request
# English labels/text wherever the application uses this setting.
# -----------------------------------------------------------------------------
MAX_PER_RUN = int(os.getenv("MAX_PER_RUN", "25"))
NOTIFY_LANGUAGE = os.getenv("NOTIFY_LANGUAGE", "ar").strip().lower()
LANGUAGE = NOTIFY_LANGUAGE  # compatibility alias for code expecting LANGUAGE
SOURCE_BUTTON = os.getenv("SOURCE_BUTTON", "true").strip().lower() in {
    "1", "true", "yes", "y", "on"
}

# -----------------------------------------------------------------------------
# Local storage.
# -----------------------------------------------------------------------------
DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DB_PATH = DATA_DIR / "jobs.db"

# -----------------------------------------------------------------------------
# LLM evaluation and rewriting instructions (converted from YAML `criteria`).
# -----------------------------------------------------------------------------
CRITERIA = """GOAL
Find technology and software job offers. Accept any tech or software role, at any seniority,
location, work mode, or employment type.

ACCEPT: ANY TECH OR SOFTWARE JOB
Software developers and engineers, full-stack, backend, frontend, mobile and web developers;
AI, ML, LLM and data roles; data analysts and BI; DevOps, SRE and cloud; cybersecurity;
QA and testing; game development; embedded and firmware; IT support, help desk, systems,
network and sysadmin roles; technical leads and managers; UI/UX for software products;
software product/project managers; and technology freelance work.
Arabic job titles count too.
Never reject a tech job because of its location, country restrictions, visa requirements,
work mode, salary, seniority or technology stack.
If a post advertises multiple jobs, accept it if at least one of them is a tech role.

REJECT ALWAYS
- Non-tech jobs, including sales, marketing, accounting, finance, non-IT banking, HR, legal,
  administration, procurement, logistics, drivers, secretaries, non-IT customer support,
  drilling, non-software engineering, video editing, social media, data entry, medical,
  teaching, construction, hospitality and hardware repair.
- Scams, application fees, deposits, MLM, forex/crypto trading schemes and suspicious
  earnings promises.
- Posts with no identifiable company that provide only a private WhatsApp/Telegram contact.
- Courses, bootcamps, advertisements, news, personal CVs and requests for employment.

SCORING
3 = Software development or engineering, including developers, engineers and programmers.
2 = Other clear technology roles, including data, AI, DevOps, security, QA, networking,
    embedded systems and technical management.
1 = Borderline or less clearly defined tech roles, including IT support, analysts and UI/UX.
0 = Reject.
Include every genuine tech job with score 1, 2 or 3.

POST REWRITING RULES — MANDATORY
Your task is to REWRITE THE ORIGINAL JOB POST, not create a new job advertisement,
summarize it in a different format, or explain it to the reader.

1. LANGUAGE
- Write the entire rewritten post in natural, professional Arabic.
- This rule applies even when the original post is in English.
- Use Arabic for descriptions, requirements, responsibilities, benefits, instructions and labels.
- Keep programming languages, frameworks, libraries, software tools, technical stacks,
  technical methodologies, abbreviations and recognized technical terms in English.
- Examples: Python, JavaScript, React, Next.js, Django, FastAPI, Docker, AWS, Git,
  Machine Learning, Deep Learning, RAG, LLM, DevOps, QA, UI/UX, IT Help Desk.
- Do not replace technical terms with Arabic transliterations. Write Python, not بايثون;
  React, not رياكت; Docker, not دوكر.
- Keep company names, official job titles, product names and other proper names unchanged.
- The original job title may remain in English. Translate the surrounding descriptive text
  into Arabic.

2. FAITHFUL REWRITING ONLY
- Preserve the original post's meaning, information, sequence and relevant details.
- Improve readability, spelling, punctuation and formatting without changing the content.
- Do not add a new summary, introduction, conclusion, recommendation, explanation or opinion.
- Do not invent responsibilities, requirements, experience levels, salary, benefits, gender,
  company information, location, contact details or any other information.
- Never add fields that are absent from the original post.
- Do not assume that missing information is "not specified" and add it as a new field.
- Do not omit existing information merely because it seems unimportant.
- Do not turn a direct rewrite into a generic job template.

3. LINKS AND APPLICATION INSTRUCTIONS
- Preserve every relevant original URL exactly as provided.
- Preserve the purpose and association of each link.
- An application link must remain associated with applying for the job.
- App Store and Google Play links must remain associated with downloading the application.
- Do not group every link under "Contact", and do not invent contact methods.
- Preserve relevant link labels, deadlines and application instructions.
- Do not generate new links or replace original links with guessed URLs.

4. FORMATTING
- Keep the original post's structure where practical.
- Use short, readable Arabic text suitable for Telegram.
- Retain useful original emojis and section divisions without adding decorative clutter.
- Keep technical hashtags and technology names in English when they exist in the source.
- Do not use English headings such as "Requirements", "Contact", "Gender" or "Location"
  when an Arabic heading is appropriate.
- Do not add a gender field or any other template field unless that information is
  explicitly present in the original post.
- Output only the rewritten post in formatted_message. The post must contain no evaluation
  score, rejection reason, model commentary or explanation of what was changed.

5. REFERENCE EXAMPLE

Original:
🔹 الشاغر الوظيفي: IT Help Desk
🔹 الناشر: Miamed
متطلبات الفرصة:
1. شهادة جامعية في علوم الحاسوب أو ما يعادلها.
2. فهم قوي لأنظمة الحاسوب والبرامج والأجهزة.
قدم الآن على الشاغر من هنا:
https://forsa.sy/forsa-details.html?id=7ea2bdba-b186-4648-aff1-25cdd7d92ea2
حمل تطبيق فرصة للتوظيف الآن:
App Store: https://apps.apple.com/ae/app/forsa/id1531619672
Direct Link: http://bit.ly/38qG06H
Google Play: http://bit.ly/3r0O6t3

Correct rewrite:
🔹 الشاغر الوظيفي: IT Help Desk

🔹 الناشر: Miamed

📋 متطلبات الفرصة:
1. شهادة جامعية في علوم الحاسوب أو ما يعادلها.
2. فهم قوي لأنظمة الحاسوب والبرامج والأجهزة.

🔹 للتقديم على الشاغر:
https://forsa.sy/forsa-details.html?id=7ea2bdba-b186-4648-aff1-25cdd7d92ea2

🔹 تحميل تطبيق فرصة للتوظيف:
App Store: https://apps.apple.com/ae/app/forsa/id1531619672
Direct Link: http://bit.ly/38qG06H
Google Play: http://bit.ly/3r0O6t3

6. OUTPUT FORMAT
Return ONLY one valid JSON object with exactly these keys:
{
  "score": 2,
  "status": "accept",
  "reason": "Brief internal classification only",
  "formatted_message": "The faithful Arabic rewrite of the original post"
}

score must be an integer from 0 to 3.
status must be "accept" for scores 1, 2 or 3, and "reject" for score 0.
reason is internal metadata only; never include it in formatted_message.
formatted_message must contain only the rewritten post, with no extra explanation.
Escape newline characters and quotation marks correctly so the response is valid JSON.
Do not return Markdown fences or any text outside the JSON object."""


def require(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise SystemExit(f"Missing environment variable {name}. See .env.example.")
    return value


def log(message: str) -> None:
    print(f"[{datetime.now():%H:%M:%S}] {message}", flush=True)
