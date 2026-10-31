# Start here: the simplest way to run the project for the first time

You need: a free GitHub account and a web browser. Nothing is installed on your computer.

## 1. Put the code on GitHub (5 minutes)
1. Go to github.com, click **New repository**, name it `tech-task`, keep it **Private**, click **Create repository**.
2. Unzip `tech-task.zip` on your computer. On the new repository page click **uploading an existing file**, drag in the *contents*
   of the unzipped `tech-task` folder (the `backend`, `frontend`, `docs`, `scripts` folders and the files beside them), and click **Commit changes**.
   (Do not upload a `.env` file. There is none in the zip.)

## 2. Open it in a browser-based computer (Codespaces)
1. On the repository page click the green **Code** button, then the **Codespaces** tab, then **Create codespace on main**.
2. Wait a few minutes until you see a code editor with a terminal at the bottom. If it shows an error while building, copy the
   error text and send it to Claude.

## 3. Run everything once
In the terminal at the bottom type exactly:
```
bash scripts/first_run.sh
```
Wait until it prints a SUMMARY (it can take 10 to 20 minutes the first time). Failures are expected on a first run; they are normal and fixable.

## 4. Send the result
In the same terminal type:
```
python3 scripts/summarize_log.py
```
Copy everything it prints and paste it to Claude. That is all that is needed. Claude will fix the failures and tell you what to re-run.

## 5. After the fixes
Upload the fixed files Claude gives you (or ask for a new zip), then run step 3 again until the SUMMARY shows every step ok.
Then run `python3 scripts/audit.py` any time to see what is still missing for the submission.

## If Codespaces is not available to you
Install Docker Desktop (and Node.js 24 if you can), open a terminal in the project folder and run the same two commands. On Windows use WSL2.
If something blocks you, copy the exact error message and send it to Claude together with your operating system.
