# UI demo walkthrough

Start from the story we want to demonstrate, perform it in the iOS UI, and use failures to choose the next implementation work. Repository checkboxes track implementation only. A successful build, API health check, or scripted backend response does not establish that the corresponding UI journey works.

## Record each run

Record the commit, device/iOS version, backend URL (no keys), date, project and meeting names, screenshots, and observed results. Use **Passed**, **Failed**, **Blocked**, or **Not run** for each step. Mark Passed only after performing the action and observing its result. A local fixture run and a connected backend run are separate evidence.

## Demo story and acceptance criteria

Use a real server project with at least two completed recordings and a second project for the scope check. Choose a question whose answer and source timestamp you can verify in the transcript, plus an unsupported question. Obtain recording consent before uploading.

| Step | UI action | Expected result | Latest evidence |
| --- | --- | --- | --- |
| 1 | Launch and enter the app | Identify placeholder login honestly; it does not establish a real account or isolated user data | Not run |
| 2 | Open Meetings | Server projects appear; local sample projects are clearly identified | Reported failure: sample projects looked like real projects |
| 3 | Create a project and upload a recording with consent | Processing completes; the recording appears under the intended project | Not run |
| 4 | Open the completed meeting | Summary, transcript, decisions, and candidates match the uploaded recording | Not run |
| 5 | Open Chat before opening every project detail | Project picker distinguishes samples; selecting a server project loads its meetings directly | Reported gap: Chat relied on meetings previously cached by Meetings |
| 6 | Select a project and open the meeting selector | Completed meetings can be selected; unfinished meetings are visible but unavailable; All meetings is explicitly scoped to this project | Not run |
| 7 | Ask the supported question across the project's meetings | Answer includes a citation to the correct meeting and timestamp; verify its wording against the transcript | Not run |
| 8 | Select one meeting and ask again | New conversation uses only the selected meeting | Not run |
| 9 | Ask the unsupported question | Honest refusal without invented evidence | Not run |
| 10 | Switch to the second project and ask about the first | No evidence from the first project is returned | Not run |
| 11 | Open history, relaunch, and reopen the thread | Saved messages and their original project/meeting scope survive | Not run |
| 12 | Approve a candidate with a due date, then open Tasks | Approved task appears on the correct date; done and undo persist after refresh | Not run |
| 13 | Disconnect the backend and open Chat | Refresh failure is visible; retry recovers after reconnection | Not run |

## Work backward from failures

Fix the earliest failing step needed for the story, repeat that step in the UI, then continue the walkthrough. Keep unverified rows marked Not run. Do not fill missing behavior with sample content or silently treat another API request as UI evidence.

Playback/seek, per-attendee storylines, real login, voice identity, and cross-project search are outside this initial demo's verified claims. Add acceptance steps before presenting them as working.
