# Run the meeting assistant UI locally

This is a clickable prototype of the meeting-assistant UI. It uses mock meeting/task/chat data, so you do **not** need a Gemini API key or the Python CLI to try it.

**Repo:** [https://github.com/BryanDYang/agent-accountability-lab](https://github.com/BryanDYang/agent-accountability-lab)  
**Branch:** `feature/meeting-ui-draft`

---

## What you need first

1. **Git** (already installed if you use GitHub)
2. **Node.js 18 or newer** (this also installs `npm`)

Check that both work:

```bash
git --version
node -v
npm -v
```

If Node is missing, install it from [nodejs.org](https://nodejs.org/).

---

## Option A: You do not have the repo yet

Open a terminal and run:

```bash
git clone -b feature/meeting-ui-draft https://github.com/BryanDYang/guardian-agent.git
cd guardian-agent/meeting-assistant-ui
npm install
npm run dev
```

Then open **[http://localhost:3000](http://localhost:3000)** in your browser.

---



## Option B: You already cloned the repo

From the repo folder:

```bash
git fetch origin
git checkout feature/meeting-ui-draft
git pull
cd meeting-assistant-ui
npm install
npm run dev
```

Then open **[http://localhost:3000](http://localhost:3000)** in your browser.

---



## What you should see

The app looks like a phone-sized preview with three tabs:

- **Meetings** — mock meeting list and details
- **Tasks** — mock action items
- **Chat** — mock chat with the assistant

Leave the terminal open while you use the app. To stop the server, press **Ctrl+C**.

---



## If something goes wrong


| Problem                                                  | What to try                                                                        |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| `command not found: node` or `npm`                       | Install Node.js 18+, then open a new terminal                                      |
| `could not find path` / no `meeting-assistant-ui` folder | Make sure you are on branch `feature/meeting-ui-draft` (`git branch`)              |
| Port 3000 is already in use                              | Stop the other app using that port, or tell a teammate so they can change the port |
| `npm install` fails                                      | Delete `node_modules` and try `npm install` again                                  |


You do **not** need to copy `.env.example` or set `GEMINI_API_KEY` to browse this prototype.