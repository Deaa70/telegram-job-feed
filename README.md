# Telegram Job Feed

Turn the noisy job channels you follow on Telegram into one clean feed of **tech jobs**.

Once a day it reads the channels you choose, keeps only real tech job offers, pulls out the important details
of each one (company, role, location, requirements, salary, contacts ...), and posts them as tidy, uniform
messages in a private Telegram channel of your own. Applying stays manual: you read the feed and contact the
employers yourself.

## What you get

Every job arrives in the same format. The message body is written in **Arabic**, while technical terms
(programming languages, frameworks, tools, company names, job titles, currencies) stay in their original
form, usually English. Sections without data are left out, every contact is on its own line.

```text
Network and Systems Engineer
🏢 Example Foundation

📍 دبي، الإمارات · حضوري
🛂 تأشيرة مقدمة
💼 دوام كامل
⏱ ساعات العمل: 8 ساعات يومياً، من الأحد إلى الخميس
👥 الجنس: ذكر أو أنثى
💰 الراتب: 15,000 AED
📅 آخر موعد للتقديم: 30 نوفمبر 2026

📝 نبذة
المؤسسة تبحث عن مهندس شبكات وأنظمة لمكتبها في دبي.

✅ المسؤوليات
• إدارة شبكة المكتب
• مراقبة السيرفرات

📋 المتطلبات
• درجة البكالوريوس في IT
• خبرة 3+ سنوات

🛠 التقنيات: Cisco, Linux

📞 التواصل
✉️ careers@example.com
🔗 https://example.com/careers/network-engineer
```

## How it works

```text
your job channels ──▶ read the latest posts ──▶ LLM: is it a tech job? ──▶ LLM: extract the details ──▶ your private channel
```

1. **Read.** A normal Telegram account (read-only) reads the newest posts of the channels listed in
   `settings.py`. It also collects links hidden behind words or buttons, which is where many channels put the
   "apply" link.
2. **Filter.** The posts go to an LLM in small batches. It returns only the numbers of the posts that are tech
   jobs. Ads, courses, scams and non-tech jobs are dropped.
3. **Extract.** Each remaining post is sent to the LLM on its own (so details of different jobs never get mixed)
   and turned into a structured record. The LLM also double-checks that the job is really a tech job, and writes
   the descriptive text in Arabic while keeping technical terms in English.
4. **Post.** Your Telegram bot publishes one message per job in your private channel. The message is formatted
   with Arabic section labels and no inline button.

Safeguards against made-up information:
- Phone numbers, emails, @handles and links are found with regular expressions in the code, never by the LLM.
- Salary, working hours, contract duration and deadline are dropped unless their numbers literally appear in the
  original post. Technology names are dropped unless they appear in the post.
- Gender is shown only when the post states it; otherwise it says "غير محدد".
- Posts already seen are skipped (also when the same job is cross-posted in several channels), so a job is
  never posted twice.

### Hashing and duplicate detection

Job channels cross-post the same opening across multiple channels with different headers, emojis and
formatting. To avoid paying the LLM twice and posting the same job multiple times, the pipeline uses two
cheap, local, pure-Python checks. Neither layer makes any additional LLM calls.

**Layer 1 — `text_hash`.** As soon as a post is read, its text is normalized (whitespace collapsed,
lowercased) and hashed with SHA-256. If the hash already exists in the `jobs` table, the post is skipped
before it ever reaches the LLM. This catches byte-identical forwards and reposts.

**Layer 2 — `signature`.** After the LLM extracts the structured record, a second hash is built from the
job's stable fields: `company`, `city`, `country`, `salary` (digits only), `job_type`, and the first five
words of `title`. Each field is normalized (Arabic-Indic digits translated to ASCII, punctuation and emojis
stripped, lowercase), only present fields are included, and they are sorted as `key=value` pairs. At least
three fields must be present, otherwise the signature is skipped — this prevents false positives between
two different jobs at the same company. If the resulting hash matches an existing row whose status is
`match` or `sent`, the new post is marked `rejected` and never reaches your channel.

Both layers run entirely on your machine and cost nothing.

## What you need

- Python 3.10 or newer.
- A Telegram account that **reads** the channels (a spare account is a good idea) and is a member of each
  channel you want to follow.
- A Telegram **bot** (free, from @BotFather) and a **private channel** where the bot posts.
- An API key for an **OpenAI-compatible LLM service** (for example OpenRouter or OpenAI). Use a reasonably
  capable model: very small models struggle with Arabic and with judging job posts.

Why a normal account for reading? A Telegram bot can only read channels where it is an administrator, so it
cannot follow channels you merely joined. A regular account can.

## Setup

### 1. Install

```bash
pip install -r requirements.txt
```

Then copy `.env.example` to `.env`. You will fill it in over the next steps. Never share or publish `.env`.

### 2. Telegram API keys (for the reading account)

1. Open https://my.telegram.org and log in with the reading account's phone number.
2. Choose **API development tools** and create an application (any title and short name).
3. Copy **App api_id** and **App api_hash** into `.env` as `API_ID` and `API_HASH`.

### 3. Log in once

```bash
python login.py
```

Enter the phone number, the code Telegram sends to the app, and the two-step password if you have one.
It prints a line `TELEGRAM_SESSION=...`: paste it into `.env`. It also prints every channel and group of the
account with the exact name to use in the next step. The session string gives full access to the account, so
keep it secret.

### 4. Choose the channels to follow

Open `settings.py` and fill `CHANNELS`. Public channels are written as `"@username"`; private ones use the
number printed by `login.py`.

### 5. Create the bot and your private channel

1. In Telegram, talk to **@BotFather**, send `/newbot`, and copy the token into `.env` as `BOT_TOKEN`.
2. Create a new **private channel**, then add your bot as an **administrator** with the **Post messages**
   permission.
3. Find the channel's numeric id: post any message in the channel, then open this address in a browser (put
   your token in place of `<TOKEN>`): `https://api.telegram.org/bot<TOKEN>/getUpdates`. Look for
   `"chat":{"id":-100...`. That number (with the minus sign) is `NOTIFY_CHAT_ID`.

### 6. Choose the LLM

Fill `LLM_API_KEY`, `LLM_MODEL` and, if you do not use OpenRouter, `LLM_BASE_URL` in `.env`.

### 7. Run it

```bash
python main.py
```

The program prints what it is doing at every step. The first run posts every tech job from the last 48 hours.

## Configuration

**`.env`** (secrets and technical settings)

| Variable | Meaning |
|---|---|
| `API_ID`, `API_HASH` | Telegram API keys of the reading account |
| `TELEGRAM_SESSION` | Login of the reading account, created by `login.py` |
| `LLM_API_KEY`, `LLM_MODEL` | Your LLM service key and model name |
| `LLM_BASE_URL` | Address of the LLM service (default: OpenRouter) |
| `BOT_TOKEN` | Token of your Telegram bot |
| `NOTIFY_CHAT_ID` | Id of the private channel where jobs are posted |
| `DATA_DIR` | Folder for the database (default `./data`; use `/data` in Docker) |
| `LOOKBACK_HOURS` | How far back every run reads (default 48) |

**`settings.py`** (what to follow and what to accept)

- `CHANNELS`: the channels and groups to read.
- `CRITERIA`: plain-language description of which jobs you want. Edit it to fit you, for example to accept only
  remote jobs or to exclude junior roles.
- Limits such as the batch size and the maximum length of a post sent to the LLM. The defaults work well.

The project is built for **tech jobs**. To follow another field, also adjust the "tech" wording in the two
prompts at the top of `llm.py`.

## Running it every day

Run `python main.py` once a day. Examples:

- **Linux or macOS (cron):** `0 8 * * * cd /path/to/project && python main.py >> run.log 2>&1`
- **Windows:** create a daily task in Task Scheduler that runs `python main.py` in the project folder.
- **Docker:** the included `Dockerfile` runs the program once and exits. Keep the `/data` folder in a persistent
  volume and start the container daily with your scheduler.

### Deploying on a VPS with Dokploy

1. Push the project (with a `Dockerfile` in the root) to your Git repository.
2. In Dokploy, create a **Project** and an **Application**, and connect the repository.
3. Set the build type to **Dockerfile**.
4. Add all variables from your local `.env` in the application's **Environment** tab. Set `DATA_DIR=/data`.
5. Under **Advanced → Mounts**, add a persistent volume and mount it at `/data`. This keeps `data/jobs.db`
   between runs so old posts are never re-posted.
6. Deploy once to build the image.
7. Open the **Schedules** tab and create a new schedule:
   - **Schedule:** `0 0 * * *` (daily at midnight) or any cron you prefer.
   - **Timezone:** pick yours, or keep UTC.
   - **Shell Type:** Bash.
   - **Command:** `python main.py`.
   - **Enabled:** on.
8. Use **Run Now** once to verify. Logs of each run are visible from the Schedules tab.

Dokploy starts the container, runs `python main.py`, and the container exits when the run finishes. The next
scheduled run starts a fresh container that reuses the `/data` volume.

Keep the `data` folder between runs: it remembers which posts were already handled. Each run also looks back 48
hours, so a missed day is covered automatically. If a run fails, the bot posts a short alert in your channel.

## Project files

| File | Purpose |
|---|---|
| `main.py` | Runs the whole pipeline once |
| `settings.py` | Your channels, your criteria, limits |
| `telegram_reader.py` | Reads the Telegram channels |
| `llm.py` | Tech filter and details extraction (writes Arabic text, keeps tech terms in English) |
| `notify.py` | Message layout (Arabic labels) and posting through the bot |
| `db.py` | Small SQLite database (`data/jobs.db`) |
| `login.py` | One-time login of the reading account |
| `Dockerfile` | Container image used for VPS / Dokploy deployment |

## Troubleshooting

- **"Missing environment variable ..."**: that value is empty in `.env`; see `.env.example`.
- **"The Telegram session is not valid anymore"**: run `python login.py` again and replace `TELEGRAM_SESSION`.
  Never use the same session string on two machines at the same time.
- **A channel is skipped ("cannot open it")**: the reading account is not a member, or the name is wrong.
  `python login.py` lists the exact names.
- **Telegram error about administrator rights or "chat not found"**: the bot must be an administrator of the
  private channel with the Post messages permission, and `NOTIFY_CHAT_ID` must be that channel's id.
- **No jobs appear**: your channels may post few tech jobs, or your `CRITERIA` may be too strict. Try a more
  capable `LLM_MODEL` first.
- **Non-tech jobs slip through or tech jobs are missed**: use a stronger model, and make `CRITERIA` more specific.
- **Messages are in English instead of Arabic**: use a model with good Arabic output, and confirm that the
  "Write all descriptive text values in natural, professional Arabic" rule is present in `DETAILS_PROMPT` inside
  `llm.py`. Rows already extracted keep their old details; clear `data/jobs.db` or delete the pending rows to
  re-extract them.
- **The same job appears twice**: the second copy had no company, or fewer than three signature fields, so it
  could not be matched. See the "Hashing and duplicate detection" section above.
- **A volume is not persisting**: check that the Dokploy mount path is `/data` and `DATA_DIR=/data` in the
  environment. Without this, the SQLite file is lost on each container restart.
- **my.telegram.org shows an error when creating the app**: try again later, from a different network, without a
  VPN or proxy.

## Good to know

- It uses Telegram's official API with a normal account in read-only mode (it never sends, joins or leaves
  anything). Telegram's terms still apply; use your own account responsibly.
- The only recurring cost is the LLM service. A daily run needs a few requests plus one per tech job.
- Jobs are extracted by an LLM from free-text posts, so mistakes are possible. Check important details with the
  employer before applying.
- Stored data: the posts that were read and the extracted details, kept in `data/jobs.db` on your machine (or on
  the mounted `/data` volume when running in Docker).

## Developer

 [**Deaa Dev**](https://deaa.vercel.app)