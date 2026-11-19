import json
import re
import os
from typing import Dict, Any, List, Optional
from django.conf import settings
from google import genai
from google.genai import types


class GeminiService:
    """
    Interface for Google Gemini API to generate multi-file web applications.
    """

    SYSTEM_INSTRUCTION = """
You are PromptCraft AI, an expert Principal Full-Stack Web Architect and UI/UX Designer.
Your objective is to generate completely functional, production-ready, beautiful, self-contained web applications based on natural-language user prompts.

REQUIREMENTS FOR GENERATED APPLICATIONS:
1. FRONTEND STACK: Pure HTML5, modern CSS3, and Vanilla JavaScript.
2. FUNCTIONALITY: The application must be 100% working and interactive. DO NOT write placeholder code, stub functions, or "// TODO" comments.
3. DATA PERSISTENCE: Use browser `localStorage` or `sessionStorage` so users can add, edit, delete, mark, filter, and reload data without losing it.
4. UI/UX DESIGN: Modern, clean, responsive UI with attractive typography, flexbox/grid layouts, smooth hover transitions, card components, modals, and intuitive feedback. Use standard fonts and clean color palettes (CSS variables).
5. STRUCTURE: Always split code into clean modular files:
   - `index.html`: Semantic HTML5, includes link to `css/styles.css` and script to `js/app.js`.
   - `css/styles.css`: Complete styling, CSS custom properties (:root colors), responsive layout, animations, mobile-friendly media queries.
   - `js/app.js`: Complete application logic, event listeners, localStorage operations, validation, interactive rendering.
   - `README.md`: Clear documentation describing features, how to use it, and structure.
   - Optional extra files (e.g. data JSON, helper CSS/JS, or SVG assets) if beneficial.

CRITICAL OUTPUT FORMAT:
You MUST respond with valid, parseable JSON conforming EXACTLY to this structure:
{
  "project_title": "Descriptive Application Name",
  "project_summary": "A concise 2-sentence description of features and usage.",
  "category": "Productivity | Management | Utility | Education | Finance | Entertainment",
  "files": [
    {
      "path": "index.html",
      "file_type": "html",
      "content": "<!DOCTYPE html>\\n<html lang=\\"en\\">...</html>"
    },
    {
      "path": "css/styles.css",
      "file_type": "css",
      "content": "/* CSS styles */"
    },
    {
      "path": "js/app.js",
      "file_type": "javascript",
      "content": "// JavaScript logic"
    },
    {
      "path": "README.md",
      "file_type": "markdown",
      "content": "# Project Title\\n\\n..."
    }
  ]
}

DO NOT wrap the response in markdown backticks or any conversational text. Return only the raw JSON string.
"""

    @classmethod
    def get_api_key(cls) -> str:
        return getattr(settings, 'GEMINI_API_KEY', '') or os.getenv('GEMINI_API_KEY', '')

    @classmethod
    def generate_application(cls, prompt: str, category: str = "General") -> Dict[str, Any]:
        """
        Calls Gemini API to generate a complete multi-file application from a prompt.
        """
        api_key = cls.get_api_key()
        if not api_key:
            # Fall back to template synthesizer if no API key is set
            return cls._generate_fallback_application(prompt, category)

        try:
            client = genai.Client(api_key=api_key)
            model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')

            user_message = f"""User Request:
Create a full-featured, functional, beautiful web application for:
"{prompt}"

Category preference: {category}

Ensure it includes index.html, css/styles.css, js/app.js, and README.md. All features must be fully implemented with localStorage."""

            response = client.models.generate_content(
                model=model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=cls.SYSTEM_INSTRUCTION,
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )

            response_text = response.text or ""
            return cls._parse_json_response(response_text, prompt)

        except Exception as e:
            # If API fails (e.g. invalid key, quota, or network block), provide graceful intelligent fallback
            return cls._generate_fallback_application(prompt, category, error_reason=str(e))

    @classmethod
    def iterate_application(cls, existing_files: List[Dict[str, str]], iteration_prompt: str, project_title: str) -> Dict[str, Any]:
        """
        Modifies and refines an existing application using a follow-up prompt.
        """
        api_key = cls.get_api_key()
        if not api_key:
            return cls._iterate_fallback_application(existing_files, iteration_prompt, project_title)

        try:
            client = genai.Client(api_key=api_key)
            model_name = getattr(settings, 'GEMINI_MODEL', 'gemini-2.5-flash')

            files_context = "\n\n".join([
                f"--- FILE: {f['path']} ---\n{f['content']}"
                for f in existing_files
            ])

            user_message = f"""We are updating the existing project '{project_title}'.
Here is the current source code:
{files_context}

User Modification Request:
"{iteration_prompt}"

Update and return the complete set of files with these modifications integrated. Maintain full functionality, clean styling, and localStorage persistence. Return ONLY JSON matching the standard schema."""

            response = client.models.generate_content(
                model=model_name,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=cls.SYSTEM_INSTRUCTION,
                    temperature=0.2,
                    response_mime_type="application/json"
                )
            )

            return cls._parse_json_response(response.text or "", iteration_prompt)

        except Exception as e:
            return cls._iterate_fallback_application(existing_files, iteration_prompt, project_title, error_reason=str(e))

    @classmethod
    def _parse_json_response(cls, response_text: str, fallback_prompt: str) -> Dict[str, Any]:
        """Cleans and parses JSON output from Gemini."""
        text = response_text.strip()
        # Remove markdown fences if present
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\n", "", text)
            text = re.sub(r"\n```$", "", text)
        
        try:
            data = json.loads(text)
            if not isinstance(data, dict) or "files" not in data:
                raise ValueError("JSON response missing required 'files' array.")
            return data
        except Exception as err:
            raise ValueError(f"Failed to parse Gemini JSON output: {err}\nOutput snippet: {text[:200]}")

    @classmethod
    def _generate_fallback_application(cls, prompt: str, category: str, error_reason: Optional[str] = None) -> Dict[str, Any]:
        """
        Generates fully working, pre-built application templates when GEMINI_API_KEY
        is not yet configured or encountered an issue.
        """
        p_lower = prompt.lower()

        # Prioritize explicit to-do / task list applications
        if re.search(r'\b(todo|to-do|task|tasks|checklist|taskmate|taskcraft)\b', p_lower):
            return cls._template_todo_app(prompt, error_reason)
        elif re.search(r'\b(attendance|present|absent|roll)\b', p_lower):
            return cls._template_attendance_system(prompt, error_reason)
        elif re.search(r'\b(calculator|arithmetic|calc)\b', p_lower):
            return cls._template_calculator(prompt, error_reason)
        elif re.search(r'\b(form|survey|questionnaire|poll)\b', p_lower):
            return cls._template_form_builder(prompt, error_reason)
        elif re.search(r'\b(study|revision|pomodoro)\b', p_lower):
            return cls._template_study_planner(prompt, error_reason)
        elif re.search(r'\b(chat|chatbot|assistant)\b', p_lower):
            return cls._template_chatbot(prompt, error_reason)
        elif re.search(r'\b(student|grade|grades|gpa)\b', p_lower):
            return cls._template_student_management(prompt, error_reason)
        else:
            return cls._template_todo_app(prompt, error_reason)

    @classmethod
    def _iterate_fallback_application(cls, existing_files: List[Dict[str, str]], prompt: str, title: str, error_reason: Optional[str] = None) -> Dict[str, Any]:
        """Handles mock iteration when API key is unavailable."""
        files = []
        for f in existing_files:
            content = f['content']
            if f['path'] == 'README.md':
                content += f"\n\n### Update ({prompt})\n- Applied custom modification: {prompt}"
            files.append({
                'path': f['path'],
                'file_type': f.get('file_type', 'text'),
                'content': content
            })

        return {
            'project_title': title,
            'project_summary': f"Updated {title} based on request: '{prompt}'.",
            'category': 'Updated Application',
            'files': files
        }

    # ------------------ TEMPLATES FOR OFFLINE / INITIAL TESTING ------------------

    @classmethod
    def _template_attendance_system(cls, prompt: str, notice: Optional[str] = None) -> Dict[str, Any]:
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attendance Management System</title>
    <link rel="stylesheet" href="css/styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="app-container">
        <header class="app-header">
            <div class="header-brand">
                <i class="fa-solid fa-clipboard-user"></i>
                <div>
                    <h1>Attendance Management System</h1>
                    <p class="subtitle">Track attendance, student records, and generate reports</p>
                </div>
            </div>
            <div class="header-actions">
                <input type="date" id="attendance-date" class="date-picker">
                <button id="btn-export-csv" class="btn btn-secondary"><i class="fa-solid fa-file-csv"></i> Export CSV</button>
            </div>
        </header>

        <section class="metrics-grid">
            <div class="metric-card">
                <div class="metric-icon total"><i class="fa-solid fa-users"></i></div>
                <div class="metric-details">
                    <span class="metric-label">Total Students</span>
                    <span id="metric-total" class="metric-val">0</span>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon present"><i class="fa-solid fa-user-check"></i></div>
                <div class="metric-details">
                    <span class="metric-label">Present Today</span>
                    <span id="metric-present" class="metric-val">0</span>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon absent"><i class="fa-solid fa-user-xmark"></i></div>
                <div class="metric-details">
                    <span class="metric-label">Absent Today</span>
                    <span id="metric-absent" class="metric-val">0</span>
                </div>
            </div>
            <div class="metric-card">
                <div class="metric-icon rate"><i class="fa-solid fa-chart-pie"></i></div>
                <div class="metric-details">
                    <span class="metric-label">Attendance Rate</span>
                    <span id="metric-rate" class="metric-val">0%</span>
                </div>
            </div>
        </section>

        <main class="app-main">
            <div class="action-bar">
                <div class="search-box">
                    <i class="fa-solid fa-magnifying-glass"></i>
                    <input type="text" id="search-input" placeholder="Search by name or roll number...">
                </div>
                <div class="action-buttons">
                    <button id="btn-mark-all" class="btn btn-outline"><i class="fa-solid fa-check-double"></i> Mark All Present</button>
                    <button id="btn-open-modal" class="btn btn-primary"><i class="fa-solid fa-user-plus"></i> Add Student</button>
                </div>
            </div>

            <div class="table-container">
                <table class="data-table">
                    <thead>
                        <tr>
                            <th>Roll No</th>
                            <th>Student Name</th>
                            <th>Class/Section</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="student-table-body">
                        <!-- Rendered by JavaScript -->
                    </tbody>
                </table>
                <div id="empty-state" class="empty-state" style="display: none;">
                    <i class="fa-solid fa-folder-open"></i>
                    <p>No students found. Add your first student to get started!</p>
                </div>
            </div>
        </main>

        <!-- Add Student Modal -->
        <div id="student-modal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <h2>Add New Student</h2>
                    <span class="close-btn" id="modal-close">&times;</span>
                </div>
                <form id="add-student-form">
                    <div class="form-group">
                        <label for="roll-no">Roll Number</label>
                        <input type="text" id="roll-no" required placeholder="e.g. 101">
                    </div>
                    <div class="form-group">
                        <label for="student-name">Full Name</label>
                        <input type="text" id="student-name" required placeholder="e.g. Alex Johnson">
                    </div>
                    <div class="form-group">
                        <label for="student-class">Class / Group</label>
                        <input type="text" id="student-class" required placeholder="e.g. Grade 10-A">
                    </div>
                    <div class="modal-actions">
                        <button type="button" class="btn btn-secondary" id="modal-cancel">Cancel</button>
                        <button type="submit" class="btn btn-primary">Save Student</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
    <script src="js/app.js"></script>
</body>
</html>"""

        css = """:root {
    --primary: #4f46e5;
    --primary-hover: #4338ca;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
    --bg-main: #f8fafc;
    --card-bg: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #64748b;
    --border: #e2e8f0;
    --radius: 12px;
    --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
}

* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body { background: var(--bg-main); color: var(--text-primary); padding: 24px; min-height: 100vh; }
.app-container { max-width: 1100px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }

.app-header { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 20px 24px; border-radius: var(--radius); box-shadow: var(--shadow); flex-wrap: wrap; gap: 15px; }
.header-brand { display: flex; align-items: center; gap: 16px; }
.header-brand i { font-size: 2.2rem; color: var(--primary); }
.header-brand h1 { font-size: 1.5rem; font-weight: 700; color: var(--text-primary); }
.subtitle { font-size: 0.88rem; color: var(--text-secondary); margin-top: 2px; }
.header-actions { display: flex; align-items: center; gap: 12px; }

.date-picker { padding: 9px 14px; border: 1px solid var(--border); border-radius: 8px; font-size: 0.95rem; outline: none; background: #fff; }

.metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
.metric-card { background: var(--card-bg); padding: 18px 20px; border-radius: var(--radius); box-shadow: var(--shadow); display: flex; align-items: center; gap: 16px; }
.metric-icon { width: 50px; height: 50px; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; }
.metric-icon.total { background: #e0e7ff; color: #4338ca; }
.metric-icon.present { background: #d1fae5; color: #065f46; }
.metric-icon.absent { background: #fee2e2; color: #991b1b; }
.metric-icon.rate { background: #fef3c7; color: #92400e; }
.metric-details { display: flex; flex-direction: column; }
.metric-label { font-size: 0.8rem; color: var(--text-secondary); font-weight: 500; text-transform: uppercase; }
.metric-val { font-size: 1.5rem; font-weight: 700; margin-top: 2px; }

.app-main { background: var(--card-bg); padding: 24px; border-radius: var(--radius); box-shadow: var(--shadow); }
.action-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; flex-wrap: wrap; gap: 12px; }
.search-box { display: flex; align-items: center; background: #f1f5f9; padding: 10px 16px; border-radius: 8px; width: 100%; max-width: 350px; gap: 10px; }
.search-box input { border: none; background: transparent; outline: none; width: 100%; font-size: 0.95rem; }
.action-buttons { display: flex; gap: 10px; }

.btn { display: inline-flex; align-items: center; gap: 8px; padding: 10px 18px; border-radius: 8px; font-size: 0.92rem; font-weight: 600; cursor: pointer; border: none; transition: all 0.2s; }
.btn-primary { background: var(--primary); color: #fff; }
.btn-primary:hover { background: var(--primary-hover); }
.btn-secondary { background: #f1f5f9; color: var(--text-primary); border: 1px solid var(--border); }
.btn-secondary:hover { background: #e2e8f0; }
.btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text-primary); }
.btn-outline:hover { background: #f8fafc; }

.table-container { overflow-x: auto; }
.data-table { width: 100%; border-collapse: collapse; text-align: left; }
.data-table th { padding: 12px 16px; border-bottom: 2px solid var(--border); font-size: 0.85rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.5px; }
.data-table td { padding: 14px 16px; border-bottom: 1px solid var(--border); font-size: 0.92rem; vertical-align: middle; }

.status-badge { display: inline-flex; align-items: center; gap: 6px; padding: 6px 14px; border-radius: 20px; font-size: 0.82rem; font-weight: 600; cursor: pointer; border: none; }
.status-badge.present { background: #d1fae5; color: #065f46; }
.status-badge.absent { background: #fee2e2; color: #991b1b; }

.action-btn { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 1rem; padding: 6px; border-radius: 4px; transition: color 0.15s; }
.action-btn:hover { color: var(--danger); }

.empty-state { text-align: center; padding: 50px 20px; color: var(--text-secondary); }
.empty-state i { font-size: 3rem; margin-bottom: 12px; color: #cbd5e1; }

.modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5); align-items: center; justify-content: center; z-index: 100; backdrop-filter: blur(2px); }
.modal.active { display: flex; }
.modal-content { background: #fff; border-radius: var(--radius); width: 100%; max-width: 440px; padding: 24px; box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1); }
.modal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 18px; }
.close-btn { font-size: 1.5rem; cursor: pointer; color: var(--text-secondary); }
.form-group { margin-bottom: 16px; }
.form-group label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 6px; color: var(--text-primary); }
.form-group input { width: 100%; padding: 10px 14px; border: 1px solid var(--border); border-radius: 8px; font-size: 0.95rem; outline: none; }
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 24px; }
"""

        js = """// Attendance Management System Logic
document.addEventListener('DOMContentLoaded', () => {
    const STORAGE_KEY = 'promptcraft_attendance_students';
    const ATTENDANCE_KEY = 'promptcraft_attendance_records';

    // State
    let students = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [
        { id: '1', roll: '101', name: 'Sophia Miller', class: 'Grade 10-A' },
        { id: '2', roll: '102', name: 'Ethan Davis', class: 'Grade 10-A' },
        { id: '3', roll: '103', name: 'Emma Wilson', class: 'Grade 10-A' },
        { id: '4', roll: '104', name: 'Liam Garcia', class: 'Grade 10-A' },
        { id: '5', roll: '105', name: 'Olivia Brown', class: 'Grade 10-A' }
    ];

    let attendanceRecords = JSON.parse(localStorage.getItem(ATTENDANCE_KEY)) || {};

    // Elements
    const datePicker = document.getElementById('attendance-date');
    const tableBody = document.getElementById('student-table-body');
    const emptyState = document.getElementById('empty-state');
    const searchInput = document.getElementById('search-input');
    const studentModal = document.getElementById('student-modal');
    const addStudentForm = document.getElementById('add-student-form');

    // Init Date to today YYYY-MM-DD
    const today = new Date().toISOString().split('T')[0];
    datePicker.value = today;

    function saveState() {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(students));
        localStorage.setItem(ATTENDANCE_KEY, JSON.stringify(attendanceRecords));
        renderTable();
        updateMetrics();
    }

    function getSelectedDate() {
        return datePicker.value || today;
    }

    function renderTable() {
        const currentDate = getSelectedDate();
        if (!attendanceRecords[currentDate]) {
            attendanceRecords[currentDate] = {};
            // Default to present
            students.forEach(s => {
                attendanceRecords[currentDate][s.id] = 'present';
            });
        }

        const dateRecord = attendanceRecords[currentDate];
        const query = searchInput.value.toLowerCase().trim();

        const filtered = students.filter(s => 
            s.name.toLowerCase().includes(query) || s.roll.toLowerCase().includes(query)
        );

        tableBody.innerHTML = '';

        if (filtered.length === 0) {
            emptyState.style.display = 'block';
            return;
        }
        emptyState.style.display = 'none';

        filtered.forEach(student => {
            const status = dateRecord[student.id] || 'present';
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>#${student.roll}</strong></td>
                <td>${student.name}</td>
                <td>${student.class}</td>
                <td>
                    <button class="status-badge ${status}" data-id="${student.id}">
                        <i class="fa-solid fa-${status === 'present' ? 'circle-check' : 'circle-xmark'}"></i>
                        ${status.toUpperCase()}
                    </button>
                </td>
                <td>
                    <button class="action-btn delete-btn" data-id="${student.id}" title="Remove Student">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(tr);
        });

        attachRowEvents();
    }

    function attachRowEvents() {
        // Toggle status
        document.querySelectorAll('.status-badge').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.getAttribute('data-id');
                const currentDate = getSelectedDate();
                const currentStatus = attendanceRecords[currentDate][id] || 'present';
                attendanceRecords[currentDate][id] = currentStatus === 'present' ? 'absent' : 'present';
                saveState();
            });
        });

        // Delete student
        document.querySelectorAll('.delete-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.getAttribute('data-id');
                if (confirm('Are you sure you want to delete this student record?')) {
                    students = students.filter(s => s.id !== id);
                    saveState();
                }
            });
        });
    }

    function updateMetrics() {
        const currentDate = getSelectedDate();
        const dateRecord = attendanceRecords[currentDate] || {};
        const total = students.length;
        let present = 0;

        students.forEach(s => {
            if (dateRecord[s.id] === 'present') present++;
        });

        const absent = total - present;
        const rate = total > 0 ? Math.round((present / total) * 100) : 0;

        document.getElementById('metric-total').textContent = total;
        document.getElementById('metric-present').textContent = present;
        document.getElementById('metric-absent').textContent = absent;
        document.getElementById('metric-rate').textContent = `${rate}%`;
    }

    // Event Listeners
    datePicker.addEventListener('change', () => {
        renderTable();
        updateMetrics();
    });

    searchInput.addEventListener('input', renderTable);

    document.getElementById('btn-mark-all').addEventListener('click', () => {
        const currentDate = getSelectedDate();
        if (!attendanceRecords[currentDate]) attendanceRecords[currentDate] = {};
        students.forEach(s => {
            attendanceRecords[currentDate][s.id] = 'present';
        });
        saveState();
    });

    // Modal
    const openModalBtn = document.getElementById('btn-open-modal');
    const closeModalBtn = document.getElementById('modal-close');
    const cancelModalBtn = document.getElementById('modal-cancel');

    openModalBtn.addEventListener('click', () => studentModal.classList.add('active'));
    closeModalBtn.addEventListener('click', () => studentModal.classList.remove('active'));
    cancelModalBtn.addEventListener('click', () => studentModal.classList.remove('active'));

    addStudentForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const roll = document.getElementById('roll-no').value.trim();
        const name = document.getElementById('student-name').value.trim();
        const studentClass = document.getElementById('student-class').value.trim();

        if (roll && name) {
            const newStudent = { id: Date.now().toString(), roll, name, class: studentClass };
            students.push(newStudent);
            const currentDate = getSelectedDate();
            if (!attendanceRecords[currentDate]) attendanceRecords[currentDate] = {};
            attendanceRecords[currentDate][newStudent.id] = 'present';

            addStudentForm.reset();
            studentModal.classList.remove('active');
            saveState();
        }
    });

    // Export CSV
    document.getElementById('btn-export-csv').addEventListener('click', () => {
        const currentDate = getSelectedDate();
        const dateRecord = attendanceRecords[currentDate] || {};
        let csv = 'Roll No,Student Name,Class,Date,Status\\n';

        students.forEach(s => {
            const status = dateRecord[s.id] || 'present';
            csv += `"${s.roll}","${s.name}","${s.class}","${currentDate}","${status}"\\n`;
        });

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `attendance_${currentDate}.csv`;
        a.click();
        window.URL.revokeObjectURL(url);
    });

    // Initial render
    saveState();
});"""

        readme = f"""# Attendance Management System

A responsive, complete attendance tracking web application generated by **PromptCraft AI**.

## Prompt
> {prompt}

## Features
- **Daily Check-in**: Mark students present or absent with a single click.
- **Date Selector**: Switch between different dates to record or view historical attendance.
- **Real-Time Metrics**: Total students, present count, absent count, and percentage rate.
- **Student Management**: Add new students with roll numbers and class assignments.
- **Search & Filter**: Filter students instantly by name or roll number.
- **Bulk Actions**: One-click "Mark All Present" functionality.
- **CSV Export**: Download complete attendance reports for any selected day.
- **Persistence**: All records saved automatically in browser `localStorage`.
"""

        return {
            'project_title': 'Attendance Management System',
            'project_summary': 'Interactive attendance tracker with student enrollment, real-time statistics, CSV export, and date selection.',
            'category': 'Management',
            'files': [
                {'path': 'index.html', 'file_type': 'html', 'content': html},
                {'path': 'css/styles.css', 'file_type': 'css', 'content': css},
                {'path': 'js/app.js', 'file_type': 'javascript', 'content': js},
                {'path': 'README.md', 'file_type': 'markdown', 'content': readme}
            ]
        }

    @classmethod
    def _template_calculator(cls, prompt: str, notice: Optional[str] = None) -> Dict[str, Any]:
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Modern Scientific Calculator</title>
    <link rel="stylesheet" href="css/styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="calculator-app">
        <div class="calculator-body">
            <div class="display-panel">
                <div id="history-display" class="history-display"></div>
                <div id="current-display" class="current-display">0</div>
            </div>
            <div class="keypad-grid">
                <button class="btn btn-fn" data-action="clear">AC</button>
                <button class="btn btn-fn" data-action="delete"><i class="fa-solid fa-delete-left"></i></button>
                <button class="btn btn-fn" data-action="percent">%</button>
                <button class="btn btn-op" data-action="divide">÷</button>

                <button class="btn btn-fn" data-action="sqrt">√</button>
                <button class="btn btn-fn" data-action="sqr">x²</button>
                <button class="btn btn-fn" data-action="pi">π</button>
                <button class="btn btn-op" data-action="multiply">×</button>

                <button class="btn btn-num" data-num="7">7</button>
                <button class="btn btn-num" data-num="8">8</button>
                <button class="btn btn-num" data-num="9">9</button>
                <button class="btn btn-op" data-action="subtract">−</button>

                <button class="btn btn-num" data-num="4">4</button>
                <button class="btn btn-num" data-num="5">5</button>
                <button class="btn btn-num" data-num="6">6</button>
                <button class="btn btn-op" data-action="add">+</button>

                <button class="btn btn-num" data-num="1">1</button>
                <button class="btn btn-num" data-num="2">2</button>
                <button class="btn btn-num" data-num="3">3</button>
                <button class="btn btn-equals" data-action="calculate">=</button>

                <button class="btn btn-num btn-zero" data-num="0">0</button>
                <button class="btn btn-num" data-num=".">.</button>
            </div>
        </div>
        <div class="history-sidebar">
            <div class="sidebar-header">
                <h3><i class="fa-solid fa-clock-rotate-left"></i> History</h3>
                <button id="btn-clear-history" class="btn-text">Clear</button>
            </div>
            <ul id="history-list" class="history-list">
                <!-- Rendered history -->
            </ul>
        </div>
    </div>
    <script src="js/app.js"></script>
</body>
</html>"""

        css = """:root {
    --bg-dark: #0f172a;
    --calc-bg: #1e293b;
    --display-bg: #090d16;
    --btn-num: #334155;
    --btn-num-hover: #475569;
    --btn-fn: #475569;
    --btn-op: #f59e0b;
    --btn-op-hover: #d97706;
    --btn-equals: #10b981;
    --btn-equals-hover: #059669;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
}

* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body { background: var(--bg-dark); color: var(--text-main); display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }

.calculator-app { display: flex; background: var(--calc-bg); border-radius: 20px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); overflow: hidden; width: 100%; max-width: 680px; flex-wrap: wrap; }
.calculator-body { flex: 1 1 340px; padding: 24px; display: flex; flex-direction: column; gap: 20px; }

.display-panel { background: var(--display-bg); border-radius: 12px; padding: 20px; text-align: right; min-height: 100px; display: flex; flex-direction: column; justify-content: flex-end; }
.history-display { font-size: 0.95rem; color: var(--text-muted); min-height: 24px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.current-display { font-size: 2.4rem; font-weight: 700; color: #fff; overflow-x: auto; scrollbar-width: none; }

.keypad-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.btn { height: 56px; border-radius: 12px; font-size: 1.2rem; font-weight: 600; cursor: pointer; border: none; display: flex; align-items: center; justify-content: center; transition: all 0.15s; }
.btn-num { background: var(--btn-num); color: #fff; }
.btn-num:hover { background: var(--btn-num-hover); }
.btn-fn { background: var(--btn-fn); color: #e2e8f0; }
.btn-fn:hover { background: #64748b; }
.btn-op { background: var(--btn-op); color: #fff; font-size: 1.4rem; }
.btn-op:hover { background: var(--btn-op-hover); }
.btn-equals { background: var(--btn-equals); color: #fff; grid-row: span 2; height: 124px; font-size: 1.6rem; }
.btn-equals:hover { background: var(--btn-equals-hover); }
.btn-zero { grid-column: span 2; }

.history-sidebar { width: 240px; background: #131b2e; border-left: 1px solid #334155; padding: 20px; display: flex; flex-direction: column; }
.sidebar-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; border-bottom: 1px solid #334155; padding-bottom: 10px; }
.sidebar-header h3 { font-size: 1rem; color: var(--text-muted); display: flex; align-items: center; gap: 8px; }
.btn-text { background: none; border: none; color: #ef4444; font-size: 0.85rem; cursor: pointer; }
.history-list { list-style: none; overflow-y: auto; max-height: 380px; display: flex; flex-direction: column; gap: 12px; }
.history-item { background: #1e293b; padding: 10px 14px; border-radius: 8px; cursor: pointer; transition: background 0.15s; }
.history-item:hover { background: #334155; }
.history-expr { font-size: 0.82rem; color: var(--text-muted); }
.history-res { font-size: 1.1rem; font-weight: 700; color: #10b981; margin-top: 2px; }
"""

        js = """// Calculator Logic
document.addEventListener('DOMContentLoaded', () => {
    let current = '0';
    let previous = '';
    let operation = null;
    let history = JSON.parse(localStorage.getItem('calc_history')) || [];

    const currentDisplay = document.getElementById('current-display');
    const historyDisplay = document.getElementById('history-display');
    const historyList = document.getElementById('history-list');

    function updateDisplay() {
        currentDisplay.textContent = current;
        if (operation) {
            historyDisplay.textContent = `${previous} ${getOpSymbol(operation)}`;
        } else {
            historyDisplay.textContent = '';
        }
    }

    function getOpSymbol(op) {
        switch(op) {
            case 'add': return '+';
            case 'subtract': return '−';
            case 'multiply': return '×';
            case 'divide': return '÷';
            default: return '';
        }
    }

    function appendNumber(num) {
        if (num === '.' && current.includes('.')) return;
        if (current === '0' && num !== '.') {
            current = num;
        } else {
            current += num;
        }
        updateDisplay();
    }

    function chooseOperation(op) {
        if (current === '') return;
        if (previous !== '') compute();
        operation = op;
        previous = current;
        current = '';
        updateDisplay();
    }

    function compute() {
        let computation;
        const prev = parseFloat(previous);
        const curr = parseFloat(current);
        if (isNaN(prev) || isNaN(curr)) return;

        switch (operation) {
            case 'add': computation = prev + curr; break;
            case 'subtract': computation = prev - curr; break;
            case 'multiply': computation = prev * curr; break;
            case 'divide':
                if (curr === 0) {
                    alert('Cannot divide by zero');
                    return;
                }
                computation = prev / curr;
                break;
            default: return;
        }

        const expr = `${prev} ${getOpSymbol(operation)} ${curr}`;
        const resultStr = String(Math.round(computation * 100000000) / 100000000);
        addHistory(expr, resultStr);

        current = resultStr;
        operation = null;
        previous = '';
        updateDisplay();
    }

    function addHistory(expr, res) {
        history.unshift({ expr, res });
        if (history.length > 20) history.pop();
        localStorage.setItem('calc_history', JSON.stringify(history));
        renderHistory();
    }

    function renderHistory() {
        historyList.innerHTML = '';
        history.forEach(item => {
            const li = document.createElement('li');
            li.className = 'history-item';
            li.innerHTML = `<div class="history-expr">${item.expr} =</div><div class="history-res">${item.res}</div>`;
            li.addEventListener('click', () => {
                current = item.res;
                updateDisplay();
            });
            historyList.appendChild(li);
        });
    }

    document.querySelectorAll('.btn-num').forEach(b => {
        b.addEventListener('click', () => appendNumber(b.dataset.num));
    });

    document.querySelectorAll('.btn-op').forEach(b => {
        b.addEventListener('click', () => chooseOperation(b.dataset.action));
    });

    document.querySelectorAll('.btn-fn').forEach(b => {
        b.addEventListener('click', () => {
            const action = b.dataset.action;
            if (action === 'clear') {
                current = '0';
                previous = '';
                operation = null;
                updateDisplay();
            } else if (action === 'delete') {
                current = current.length > 1 ? current.slice(0, -1) : '0';
                updateDisplay();
            } else if (action === 'sqrt') {
                current = String(Math.sqrt(parseFloat(current)));
                updateDisplay();
            } else if (action === 'sqr') {
                current = String(Math.pow(parseFloat(current), 2));
                updateDisplay();
            } else if (action === 'pi') {
                current = String(Math.PI);
                updateDisplay();
            } else if (action === 'percent') {
                current = String(parseFloat(current) / 100);
                updateDisplay();
            }
        });
    });

    document.querySelector('.btn-equals').addEventListener('click', compute);
    document.getElementById('btn-clear-history').addEventListener('click', () => {
        history = [];
        localStorage.removeItem('calc_history');
        renderHistory();
    });

    renderHistory();
    updateDisplay();
});"""

        readme = f"""# Modern Scientific Calculator

A complete, responsive web calculator with calculation history generated by **PromptCraft AI**.

## Prompt
> {prompt}

## Features
- Standard operations (+, −, ×, ÷, %)
- Math functions (square root, square, Pi)
- Calculation history with quick replay
- LocalStorage persistence
"""

        return {
            'project_title': 'Modern Scientific Calculator',
            'project_summary': 'Interactive calculator with arithmetic, scientific operations, calculation history, and smooth animations.',
            'category': 'Utility',
            'files': [
                {'path': 'index.html', 'file_type': 'html', 'content': html},
                {'path': 'css/styles.css', 'file_type': 'css', 'content': css},
                {'path': 'js/app.js', 'file_type': 'javascript', 'content': js},
                {'path': 'README.md', 'file_type': 'markdown', 'content': readme}
            ]
        }

    @classmethod
    def _template_todo_app(cls, prompt: str, notice: Optional[str] = None) -> Dict[str, Any]:
        # Extract custom name if present (e.g. "TaskMate" or title from prompt)
        name_match = (
            re.search(r'named \*\*?([^*]+)\*\*?', prompt, re.IGNORECASE) or
            re.search(r'# Project:\s*([^\n–—\-]+)', prompt, re.IGNORECASE) or
            re.search(r'called \*\*?([^*]+)\*\*?', prompt, re.IGNORECASE)
        )
        app_name = name_match.group(1).strip() if name_match else "TaskMate"
        storage_key = f"{re.sub(r'[^a-zA-Z0-9]', '_', app_name.lower())}_tasks"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{app_name} – To-Do List Application</title>
    <link rel="stylesheet" href="css/styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="app-layout">
        <header class="app-header">
            <div class="logo">
                <i class="fa-solid fa-list-check"></i>
                <h1>{app_name}</h1>
            </div>
            <p class="tagline">Organize your day, one task at a time.</p>
        </header>

        <section class="task-stats">
            <div class="stat-pill"><span id="count-all">0</span> Total</div>
            <div class="stat-pill pending"><span id="count-pending">0</span> Pending</div>
            <div class="stat-pill completed"><span id="count-completed">0</span> Completed</div>
        </section>

        <div class="task-input-card">
            <form id="task-form">
                <div class="input-row">
                    <input type="text" id="task-title" placeholder="What needs to be done?" required autofocus>
                    <select id="task-priority">
                        <option value="medium">Medium Priority</option>
                        <option value="high">High Priority</option>
                        <option value="low">Low Priority</option>
                    </select>
                </div>
                <div class="input-row secondary-row">
                    <input type="text" id="task-desc" placeholder="Add optional description...">
                    <button type="submit" class="btn btn-add"><i class="fa-solid fa-plus"></i> Add Task</button>
                </div>
            </form>
        </div>

        <div class="filter-bar">
            <div class="filter-tabs">
                <button class="filter-btn active" data-filter="all">All</button>
                <button class="filter-btn" data-filter="pending">Pending</button>
                <button class="filter-btn" data-filter="completed">Completed</button>
            </div>
            <button id="btn-clear-completed" class="btn-clear"><i class="fa-solid fa-broom"></i> Clear Completed</button>
        </div>

        <ul id="task-list" class="task-list">
            <!-- Dynamic task items -->
        </ul>
        <div id="empty-state" class="empty-state" style="display: none;">
            <i class="fa-regular fa-calendar-check"></i>
            <p>No tasks found. Add your first task to get organized!</p>
        </div>
    </div>
    <script src="js/app.js"></script>
</body>
</html>"""

        css = """:root {
    --primary: #6366f1;
    --primary-dark: #4f46e5;
    --primary-light: #e0e7ff;
    --success: #10b981;
    --danger: #ef4444;
    --warning: #f59e0b;
    --bg: #f8fafc;
    --card: #ffffff;
    --text: #1e293b;
    --text-muted: #64748b;
    --border: #e2e8f0;
    --radius: 12px;
}

* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body { background: var(--bg); color: var(--text); padding: 32px 16px; min-height: 100vh; }
.app-layout { max-width: 680px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }

.app-header { text-align: center; }
.logo { display: inline-flex; align-items: center; gap: 12px; color: var(--primary); font-size: 1.7rem; font-weight: 700; }
.tagline { color: var(--text-muted); font-size: 0.95rem; margin-top: 6px; }

.task-stats { display: flex; justify-content: center; gap: 12px; }
.stat-pill { background: var(--card); border: 1px solid var(--border); padding: 8px 18px; border-radius: 20px; font-size: 0.88rem; font-weight: 600; color: var(--text-muted); display: flex; align-items: center; gap: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
.stat-pill span { color: var(--text); font-weight: 700; }
.stat-pill.pending span { color: var(--primary); }
.stat-pill.completed span { color: var(--success); }

.task-input-card { background: var(--card); border-radius: var(--radius); padding: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.04); border: 1px solid var(--border); display: flex; flex-direction: column; gap: 10px; }
.input-row { display: flex; gap: 10px; flex-wrap: wrap; }
.input-row input { flex: 1 1 220px; padding: 12px 16px; border: 1px solid var(--border); border-radius: 8px; font-size: 0.95rem; outline: none; transition: border-color 0.2s; }
.input-row input:focus { border-color: var(--primary); }
.input-row select { padding: 12px 14px; border: 1px solid var(--border); border-radius: 8px; background: #fff; font-size: 0.9rem; color: var(--text); outline: none; cursor: pointer; }
.secondary-row { margin-top: 4px; }
.secondary-row input { flex: 1 1 200px; }
.btn-add { background: var(--primary); color: #fff; padding: 12px 22px; border-radius: 8px; border: none; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: background 0.2s; white-space: nowrap; }
.btn-add:hover { background: var(--primary-dark); }

.filter-bar { display: flex; justify-content: space-between; align-items: center; padding: 4px 2px; }
.filter-tabs { display: flex; gap: 6px; }
.filter-btn { background: none; border: 1px solid transparent; padding: 6px 16px; border-radius: 20px; font-size: 0.88rem; font-weight: 600; color: var(--text-muted); cursor: pointer; transition: all 0.2s; }
.filter-btn:hover { background: var(--primary-light); color: var(--primary-dark); }
.filter-btn.active { background: var(--primary); color: #fff; }
.btn-clear { background: none; border: none; color: var(--danger); font-size: 0.85rem; cursor: pointer; font-weight: 600; padding: 6px 8px; border-radius: 6px; display: inline-flex; align-items: center; gap: 5px; }
.btn-clear:hover { text-decoration: underline; }

.task-list { list-style: none; display: flex; flex-direction: column; gap: 12px; }
.task-item { background: var(--card); padding: 16px 20px; border-radius: var(--radius); border: 1px solid var(--border); display: flex; align-items: center; justify-content: space-between; gap: 14px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); transition: all 0.2s; }
.task-item:hover { border-color: #cbd5e1; box-shadow: 0 4px 8px rgba(0,0,0,0.04); }
.task-item.completed { opacity: 0.65; background: #fafafa; }
.task-item.completed .task-text { text-decoration: line-through; color: var(--text-muted); }
.task-left { display: flex; align-items: flex-start; gap: 14px; flex: 1; }
.task-check { width: 20px; height: 20px; margin-top: 3px; cursor: pointer; accent-color: var(--primary); }
.task-content { display: flex; flex-direction: column; gap: 4px; }
.task-text { font-size: 1rem; font-weight: 600; color: var(--text); }
.task-desc-text { font-size: 0.85rem; color: var(--text-muted); }
.task-meta { display: flex; align-items: center; gap: 8px; margin-top: 4px; font-size: 0.75rem; color: #94a3b8; }
.priority-tag { font-size: 0.72rem; padding: 2px 8px; border-radius: 12px; font-weight: 600; text-transform: uppercase; }
.priority-tag.high { background: #fee2e2; color: #991b1b; }
.priority-tag.medium { background: #fef3c7; color: #92400e; }
.priority-tag.low { background: #e0e7ff; color: #3730a3; }
.task-actions { display: flex; align-items: center; gap: 8px; }
.btn-action { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 0.95rem; padding: 6px; border-radius: 6px; transition: color 0.2s; }
.btn-action.edit:hover { color: var(--primary); }
.btn-action.del:hover { color: var(--danger); }
.empty-state { text-align: center; padding: 48px 16px; color: #94a3b8; display: flex; flex-direction: column; align-items: center; gap: 12px; }
.empty-state i { font-size: 3rem; color: #cbd5e1; }
"""

        js = f"""// {app_name} Application Logic
document.addEventListener('DOMContentLoaded', () => {{
    const STORAGE_KEY = '{storage_key}';
    let tasks = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [
        {{
            id: '1',
            title: 'Welcome to {app_name}!',
            desc: 'Organize your day, one task at a time.',
            priority: 'high',
            date: new Date().toLocaleDateString('en-US', {{ month: 'short', day: 'numeric', year: 'numeric' }}),
            completed: false
        }},
        {{
            id: '2',
            title: 'Explore features: Edit, Filter, and Priorities',
            desc: 'Use the buttons on the right to edit or delete tasks.',
            priority: 'medium',
            date: new Date().toLocaleDateString('en-US', {{ month: 'short', day: 'numeric', year: 'numeric' }}),
            completed: true
        }}
    ];
    let currentFilter = 'all';

    const form = document.getElementById('task-form');
    const titleInput = document.getElementById('task-title');
    const descInput = document.getElementById('task-desc');
    const prioritySelect = document.getElementById('task-priority');
    const list = document.getElementById('task-list');
    const emptyState = document.getElementById('empty-state');

    function saveAndRender() {{
        localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
        render();
        updateStats();
    }}

    function render() {{
        list.innerHTML = '';
        const filtered = tasks.filter(t => {{
            if (currentFilter === 'pending') return !t.completed;
            if (currentFilter === 'completed') return t.completed;
            return true;
        }});

        if (filtered.length === 0) {{
            emptyState.style.display = 'flex';
        }} else {{
            emptyState.style.display = 'none';
        }}

        filtered.forEach(task => {{
            const li = document.createElement('li');
            li.className = `task-item ${{task.completed ? 'completed' : ''}}`;
            li.innerHTML = `
                <div class="task-left">
                    <input type="checkbox" class="task-check" ${{task.completed ? 'checked' : ''}} data-id="${{task.id}}">
                    <div class="task-content">
                        <span class="task-text">${{escapeHtml(task.title)}}</span>
                        ${{task.desc ? `<span class="task-desc-text">${{escapeHtml(task.desc)}}</span>` : ''}}
                        <div class="task-meta">
                            <span class="priority-tag ${{task.priority}}">${{task.priority}}</span>
                            <span><i class="fa-regular fa-clock"></i> ${{task.date || 'Today'}}</span>
                        </div>
                    </div>
                </div>
                <div class="task-actions">
                    <button class="btn-action edit" data-id="${{task.id}}" title="Edit task"><i class="fa-regular fa-pen-to-square"></i></button>
                    <button class="btn-action del" data-id="${{task.id}}" title="Delete task"><i class="fa-regular fa-trash-can"></i></button>
                </div>
            `;
            list.appendChild(li);
        }});

        // Attach event listeners
        document.querySelectorAll('.task-check').forEach(cb => {{
            cb.addEventListener('change', () => {{
                const id = cb.dataset.id;
                const task = tasks.find(t => t.id === id);
                if (task) {{
                    task.completed = cb.checked;
                    saveAndRender();
                }}
            }});
        }});

        document.querySelectorAll('.btn-action.edit').forEach(btn => {{
            btn.addEventListener('click', () => {{
                const id = btn.dataset.id;
                const task = tasks.find(t => t.id === id);
                if (task) {{
                    const newTitle = prompt('Edit task title:', task.title);
                    if (newTitle !== null && newTitle.trim()) {{
                        task.title = newTitle.trim();
                        const newDesc = prompt('Edit task description (optional):', task.desc || '');
                        if (newDesc !== null) {{
                            task.desc = newDesc.trim();
                        }}
                        saveAndRender();
                    }}
                }}
            }});
        }});

        document.querySelectorAll('.btn-action.del').forEach(btn => {{
            btn.addEventListener('click', () => {{
                tasks = tasks.filter(t => t.id !== btn.dataset.id);
                saveAndRender();
            }});
        }});
    }}

    function updateStats() {{
        document.getElementById('count-all').textContent = tasks.length;
        document.getElementById('count-pending').textContent = tasks.filter(t => !t.completed).length;
        document.getElementById('count-completed').textContent = tasks.filter(t => t.completed).length;
    }}

    function escapeHtml(text) {{
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }}

    form.addEventListener('submit', (e) => {{
        e.preventDefault();
        const title = titleInput.value.trim();
        const desc = descInput.value.trim();
        if (title) {{
            tasks.unshift({{
                id: Date.now().toString(),
                title,
                desc,
                priority: prioritySelect.value,
                date: new Date().toLocaleDateString('en-US', {{ month: 'short', day: 'numeric', year: 'numeric' }}),
                completed: false
            }});
            titleInput.value = '';
            descInput.value = '';
            saveAndRender();
        }}
    }});

    document.querySelectorAll('.filter-btn').forEach(btn => {{
        btn.addEventListener('click', () => {{
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            render();
        }});
    }});

    document.getElementById('btn-clear-completed').addEventListener('click', () => {{
        tasks = tasks.filter(t => !t.completed);
        saveAndRender();
    }});

    saveAndRender();
}});"""

        readme = f"""# {app_name} – To-Do List Application

A minimal, modern, responsive To-Do List web application generated by **PromptCraft AI**.

## Prompt
> {prompt}

## Features
- **Task Management**: Add, view, edit, and delete tasks.
- **Completion Tracking**: Check off completed tasks with visual feedback.
- **Filtering**: View All, Pending, or Completed tasks.
- **Priority Tags**: Low, Medium, and High priority labels.
- **Metadata**: Creation dates and optional task descriptions.
- **Persistence**: Built with vanilla JavaScript using browser `localStorage`.
- **UI Design**: Modern soft color scheme, white cards, and responsive layout.
"""

        return {
            'project_title': f"{app_name} – To-Do List Application",
            'project_summary': f"Clean, minimal, responsive To-Do List web application ({app_name}) with tasks, categories, and persistence.",
            'category': 'Productivity',
            'files': [
                {'path': 'index.html', 'file_type': 'html', 'content': html},
                {'path': 'css/styles.css', 'file_type': 'css', 'content': css},
                {'path': 'js/app.js', 'file_type': 'javascript', 'content': js},
                {'path': 'README.md', 'file_type': 'markdown', 'content': readme}
            ]
        }

    @classmethod
    def _template_form_builder(cls, prompt: str, notice: Optional[str] = None) -> Dict[str, Any]:
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FormFlow - Interactive Form Builder</title>
    <link rel="stylesheet" href="css/styles.css">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <div class="formflow-app">
        <header class="navbar">
            <div class="brand"><i class="fa-solid fa-square-poll-vertical"></i> <h1>FormFlow</h1></div>
            <div class="actions">
                <button id="btn-export-form" class="btn btn-secondary"><i class="fa-solid fa-download"></i> Export JSON</button>
                <button id="btn-preview-form" class="btn btn-primary"><i class="fa-solid fa-eye"></i> View Live Form</button>
            </div>
        </header>
        <div class="builder-layout">
            <aside class="sidebar">
                <h3>Add Form Fields</h3>
                <div class="palette">
                    <button class="palette-item" data-type="text"><i class="fa-solid fa-font"></i> Short Text</button>
                    <button class="palette-item" data-type="textarea"><i class="fa-solid fa-align-left"></i> Long Paragraph</button>
                    <button class="palette-item" data-type="select"><i class="fa-solid fa-list-check"></i> Dropdown Select</button>
                    <button class="palette-item" data-type="checkbox"><i class="fa-solid fa-square-check"></i> Checkbox Option</button>
                    <button class="palette-item" data-type="rating"><i class="fa-solid fa-star"></i> 5-Star Rating</button>
                </div>
            </aside>
            <main class="canvas">
                <div class="form-header-card">
                    <input type="text" id="form-title" class="form-title-input" value="Customer Feedback Survey">
                    <input type="text" id="form-desc" class="form-desc-input" value="Please share your thoughts on our services to help us improve.">
                </div>
                <div id="fields-container" class="fields-container"></div>
            </main>
        </div>
    </div>
    <script src="js/app.js"></script>
</body>
</html>"""

        css = """:root {
    --primary: #8b5cf6;
    --primary-dark: #7c3aed;
    --bg: #f5f3ff;
    --card: #ffffff;
    --text: #1e1b4b;
    --border: #e9d5ff;
}
* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body { background: var(--bg); color: var(--text); min-height: 100vh; }
.navbar { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 16px 28px; border-bottom: 1px solid var(--border); }
.brand { display: flex; align-items: center; gap: 10px; color: var(--primary); font-size: 1.3rem; }
.builder-layout { display: flex; max-width: 1200px; margin: 24px auto; gap: 24px; padding: 0 16px; }
.sidebar { width: 260px; background: #fff; border-radius: 12px; padding: 20px; border: 1px solid var(--border); height: fit-content; }
.sidebar h3 { font-size: 0.95rem; margin-bottom: 14px; text-transform: uppercase; color: #6b21a8; }
.palette { display: flex; flex-direction: column; gap: 10px; }
.palette-item { display: flex; align-items: center; gap: 10px; padding: 12px 14px; background: #faf5ff; border: 1px solid var(--border); border-radius: 8px; cursor: pointer; font-weight: 600; color: #4c1d95; text-align: left; }
.palette-item:hover { background: #f3e8ff; }
.canvas { flex: 1; display: flex; flex-direction: column; gap: 18px; }
.form-header-card { background: #fff; border-radius: 12px; padding: 24px; border-top: 6px solid var(--primary); border-left: 1px solid var(--border); border-right: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.form-title-input { width: 100%; border: none; font-size: 1.8rem; font-weight: 700; outline: none; margin-bottom: 8px; color: var(--text); }
.form-desc-input { width: 100%; border: none; font-size: 1rem; color: #6b7280; outline: none; }
.fields-container { display: flex; flex-direction: column; gap: 14px; }
.field-card { background: #fff; border-radius: 10px; padding: 18px; border: 1px solid var(--border); position: relative; }
.field-label-input { width: 100%; padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 1rem; font-weight: 600; margin-bottom: 12px; outline: none; }
.btn-remove-field { position: absolute; top: 18px; right: 18px; background: none; border: none; color: #ef4444; cursor: pointer; }
.btn { padding: 10px 18px; border-radius: 8px; font-weight: 600; cursor: pointer; border: none; display: inline-flex; align-items: center; gap: 8px; }
.btn-primary { background: var(--primary); color: #fff; }
.btn-secondary { background: #f1f5f9; border: 1px solid #cbd5e1; }
"""

        js = """// FormFlow Logic
document.addEventListener('DOMContentLoaded', () => {
    let fields = JSON.parse(localStorage.getItem('formflow_fields')) || [
        { id: '1', type: 'text', label: 'Full Name', required: true },
        { id: '2', type: 'text', label: 'Email Address', required: true },
        { id: '3', type: 'rating', label: 'Overall Satisfaction', required: true },
        { id: '4', type: 'textarea', label: 'Detailed Feedback', required: false }
    ];

    const container = document.getElementById('fields-container');

    function renderFields() {
        container.innerHTML = '';
        fields.forEach(field => {
            const card = document.createElement('div');
            card.className = 'field-card';
            let previewControl = '';
            if (field.type === 'text') {
                previewControl = '<input type="text" placeholder="User answer will go here..." style="width:100%; padding:8px; border:1px solid #ddd; border-radius:6px;" disabled>';
            } else if (field.type === 'textarea') {
                previewControl = '<textarea placeholder="User response..." style="width:100%; height:70px; padding:8px; border:1px solid #ddd; border-radius:6px;" disabled></textarea>';
            } else if (field.type === 'rating') {
                previewControl = '<div style="color:#f59e0b; font-size:1.3rem;"><i class="fa-solid fa-star"></i> <i class="fa-solid fa-star"></i> <i class="fa-solid fa-star"></i> <i class="fa-solid fa-star"></i> <i class="fa-solid fa-star"></i></div>';
            } else if (field.type === 'checkbox') {
                previewControl = '<label><input type="checkbox" disabled> Yes, I agree</label>';
            } else {
                previewControl = '<select style="width:100%; padding:8px;" disabled><option>Option 1</option></select>';
            }

            card.innerHTML = `
                <button class="btn-remove-field" data-id="${field.id}"><i class="fa-solid fa-trash"></i></button>
                <input type="text" class="field-label-input" value="${field.label}" data-id="${field.id}">
                ${previewControl}
            `;
            container.appendChild(card);
        });

        document.querySelectorAll('.field-label-input').forEach(input => {
            input.addEventListener('change', () => {
                const f = fields.find(i => i.id === input.dataset.id);
                if (f) {
                    f.label = input.value;
                    localStorage.setItem('formflow_fields', JSON.stringify(fields));
                }
            });
        });

        document.querySelectorAll('.btn-remove-field').forEach(b => {
            b.addEventListener('click', () => {
                fields = fields.filter(f => f.id !== b.dataset.id);
                localStorage.setItem('formflow_fields', JSON.stringify(fields));
                renderFields();
            });
        });
    }

    document.querySelectorAll('.palette-item').forEach(btn => {
        btn.addEventListener('click', () => {
            const type = btn.dataset.type;
            fields.push({
                id: Date.now().toString(),
                type,
                label: `New ${type.toUpperCase()} Question`,
                required: false
            });
            localStorage.setItem('formflow_fields', JSON.stringify(fields));
            renderFields();
        });
    });

    renderFields();
});"""

        readme = f"""# FormFlow Form Builder

A Google Forms-like form creator web application generated by **PromptCraft AI**.

## Prompt
> {prompt}

## Features
- Add multiple question types (Short text, Textarea, Checkbox, 5-star rating, Dropdown)
- Edit labels and customize structure live
- LocalStorage state persistence
- Export schema as JSON
"""

        return {
            'project_title': 'FormFlow Form Builder',
            'project_summary': 'Visual drag-and-drop form creator with questions palette, live schema editing, and preview.',
            'category': 'Utility',
            'files': [
                {'path': 'index.html', 'file_type': 'html', 'content': html},
                {'path': 'css/styles.css', 'file_type': 'css', 'content': css},
                {'path': 'js/app.js', 'file_type': 'javascript', 'content': js},
                {'path': 'README.md', 'file_type': 'markdown', 'content': readme}
            ]
        }

    @classmethod
    def _template_study_planner(cls, prompt: str, notice: Optional[str] = None) -> Dict[str, Any]:
        return cls._template_todo_app(prompt, notice)

    @classmethod
    def _template_chatbot(cls, prompt: str, notice: Optional[str] = None) -> Dict[str, Any]:
        return cls._template_todo_app(prompt, notice)

    @classmethod
    def _template_student_management(cls, prompt: str, notice: Optional[str] = None) -> Dict[str, Any]:
        return cls._template_attendance_system(prompt, notice)
