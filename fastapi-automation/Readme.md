# FastAPI Automation Tool

This FastAPI application automates various data processing tasks, including:
- Running external scripts dynamically
- Formatting files using CLI tools
- Extracting emails and credit card numbers using AI models
- Sorting JSON and processing logs
- Indexing Markdown files
- Running SQL queries on SQLite databases

The application intelligently selects whether to **call a predefined function** or **generate a Python script using AI** based on the task request.

## How It Works

1️⃣ **User Sends a Task Request**  
   - Example: *"Sort contacts in a JSON file by last name and first name."*

2️⃣ **Classification**  
   - If a predefined function exists (e.g., `sort_contacts`), it is executed.  
   - If no function exists, the app prompts an **AI model (LLM)** to generate Python code dynamically.

3️⃣ **Execution**  
   - If AI-generated code is needed, it is **saved, executed**, and results are returned.

4️⃣ **Security Measures**  
   - All operations are **restricted to the `/data` directory**.  
   - **No file deletion is allowed** to prevent accidental data loss.

## Example Task Processing

### **Task:**
*"Find all Markdown files in `/data/docs/`, extract H1 titles, and save the index in `/data/docs/index.json`."*

### **App Processing Steps:**
✅ Checks if a **predefined function** (`index_markdown`) exists.  
✅ If yes → Runs the function directly.  
✅ If no → Sends a structured **prompt** to GPT.  
✅ **GPT generates Python code** to perform the task.  
✅ The code is **executed**, and results are saved.

