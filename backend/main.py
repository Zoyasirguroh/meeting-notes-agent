from fastapi import FastAPI, WebSocket, HTTPException, BackgroundTasks, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI
import os
from datetime import datetime
import json

app = FastAPI(title="AI Meeting Notes Agent")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class TranscriptRequest(BaseModel):
    transcript: str
    meeting_platform: str
    meeting_id: Optional[str] = None

class Task(BaseModel):
    title: str
    assignee: str
    due_date: str
    priority: str
    description: Optional[str] = None

class AnalysisResult(BaseModel):
    tasks: List[Task]
    decisions: List[str]
    risks: List[str]
    follow_ups: List[str]
    summary: str

class ExportRequest(BaseModel):
    analysis: AnalysisResult
    export_to: str  # 'jira', 'trello', 'notion'

class NotificationRequest(BaseModel):
    analysis: AnalysisResult
    email: str
    slack_webhook: Optional[str] = None

# AI Analysis with OpenAI
async def analyze_transcript_with_ai(transcript: str) -> AnalysisResult:
    """Analyze meeting transcript using OpenAI GPT"""
    
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY")
    )
    
    prompt = f"""Analyze this meeting transcript and extract the following information in JSON format:

Transcript:
{transcript}

Please provide:
1. Tasks: List of actionable items with title, assignee (if mentioned), due date (if mentioned), priority, and description
2. Decisions: Key decisions made during the meeting
3. Risks: Any risks, concerns, or blockers mentioned
4. Follow-ups: Items that need follow-up or further discussion
5. Summary: A brief 2-3 sentence summary of the meeting

Return ONLY a valid JSON object with this structure:
{{
  "tasks": [
    {{
      "title": "string",
      "assignee": "string",
      "due_date": "string",
      "priority": "High|Medium|Low",
      "description": "string"
    }}
  ],
  "decisions": ["string"],
  "risks": ["string"],
  "follow_ups": ["string"],
  "summary": "string"
}}"""

    message = client.chat.completions.create(
        model="gpt-4-turbo",
        max_tokens=2000,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    
    response_text = message.choices[0].message.content
    
    # Parse JSON response
    try:
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]
        
        result = json.loads(response_text.strip())
        return AnalysisResult(**result)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse AI response: {str(e)}")

# API Endpoints
@app.post("/api/transcribe")
async def transcribe_audio(file: UploadFile):
    """Transcribe audio file using OpenAI Whisper API"""
    try:
        from openai import OpenAI
        
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="OPENAI_API_KEY not configured")
        
        client = OpenAI(api_key=api_key)
        
        # Read the audio file
        audio_content = await file.read()
        
        if not audio_content:
            raise HTTPException(status_code=400, detail="No audio data received")
        
        # Create a file-like object for OpenAI
        from io import BytesIO
        audio_file = BytesIO(audio_content)
        audio_file.name = file.filename or "audio.webm"
        
        # Transcribe using Whisper API
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=(audio_file.name, audio_file, "audio/webm")
        )
        
        return {
            "success": True,
            "transcript": transcript.text,
            "filename": file.filename
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Transcription error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

@app.post("/api/analyze")
async def analyze_meeting(request: TranscriptRequest):
    """Analyze meeting transcript and extract insights"""
    try:
        analysis = await analyze_transcript_with_ai(request.transcript)
        return {
            "success": True,
            "analysis": analysis.dict(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/jira")
async def export_to_jira(request: ExportRequest):
    """Export tasks to Jira"""
    # Jira integration
    jira_url = os.environ.get("JIRA_URL")
    jira_email = os.environ.get("JIRA_EMAIL")
    jira_token = os.environ.get("JIRA_API_TOKEN")
    jira_project = os.environ.get("JIRA_PROJECT_KEY", "PROJ")
    
    if not all([jira_url, jira_email, jira_token]):
        raise HTTPException(status_code=400, detail="Jira credentials not configured")
    
    try:
        import requests
        from requests.auth import HTTPBasicAuth
        
        auth = HTTPBasicAuth(jira_email, jira_token)
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        created_issues = []
        
        for task in request.analysis.tasks:
            # Map priority
            priority_map = {"High": "Highest", "Medium": "Medium", "Low": "Low"}
            
            issue_data = {
                "fields": {
                    "project": {"key": jira_project},
                    "summary": task.title,
                    "description": task.description or f"Task from meeting on {datetime.now().strftime('%Y-%m-%d')}",
                    "issuetype": {"name": "Task"},
                    "priority": {"name": priority_map.get(task.priority, "Medium")}
                }
            }
            
            if task.assignee and task.assignee.lower() != "team":
                # Note: You'd need to map names to Jira user IDs
                pass
            
            response = requests.post(
                f"{jira_url}/rest/api/3/issue",
                headers=headers,
                auth=auth,
                json=issue_data
            )
            
            if response.status_code == 201:
                issue = response.json()
                created_issues.append(issue["key"])
        
        return {
            "success": True,
            "message": f"Created {len(created_issues)} issues in Jira",
            "issues": created_issues
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Jira export failed: {str(e)}")

@app.post("/api/export/notion")
async def export_to_notion(request: ExportRequest):
    """Export tasks to Notion"""
    notion_token = os.environ.get("NOTION_API_TOKEN")
    notion_database_id = os.environ.get("NOTION_DATABASE_ID")
    
    if not all([notion_token, notion_database_id]):
        raise HTTPException(status_code=400, detail="Notion credentials not configured")
    
    try:
        import requests
        
        headers = {
            "Authorization": f"Bearer {notion_token}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        }
        
        created_pages = []
        
        for task in request.analysis.tasks:
            page_data = {
                "parent": {"database_id": notion_database_id},
                "properties": {
                    "Name": {"title": [{"text": {"content": task.title}}]},
                    "Assignee": {"rich_text": [{"text": {"content": task.assignee}}]},
                    "Due Date": {"rich_text": [{"text": {"content": task.due_date}}]},
                    "Priority": {"select": {"name": task.priority}},
                    "Status": {"select": {"name": "To Do"}}
                }
            }
            
            response = requests.post(
                "https://api.notion.com/v1/pages",
                headers=headers,
                json=page_data
            )
            
            if response.status_code == 200:
                created_pages.append(response.json()["id"])
        
        return {
            "success": True,
            "message": f"Created {len(created_pages)} pages in Notion",
            "pages": created_pages
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notion export failed: {str(e)}")

@app.post("/api/export/trello")
async def export_to_trello(request: ExportRequest):
    """Export tasks to Trello"""
    trello_key = os.environ.get("TRELLO_API_KEY")
    trello_token = os.environ.get("TRELLO_API_TOKEN")
    trello_board_id = os.environ.get("TRELLO_BOARD_ID")
    trello_list_id = os.environ.get("TRELLO_LIST_ID")
    
    if not all([trello_key, trello_token, trello_board_id, trello_list_id]):
        raise HTTPException(status_code=400, detail="Trello credentials not configured. Set TRELLO_API_KEY, TRELLO_API_TOKEN, TRELLO_BOARD_ID, and TRELLO_LIST_ID")
    
    try:
        import requests
        
        created_cards = []
        base_url = "https://api.trello.com/1/cards"
        
        for task in request.analysis.tasks:
            card_data = {
                "idList": trello_list_id,
                "name": task.title,
                "desc": f"Assignee: {task.assignee}\nDue Date: {task.due_date}\nPriority: {task.priority}\n\n{task.description or ''}",
                "due": task.due_date if task.due_date else None,
                "key": trello_key,
                "token": trello_token
            }
            
            # Remove None values
            card_data = {k: v for k, v in card_data.items() if v is not None}
            
            response = requests.post(base_url, json=card_data)
            
            if response.status_code == 200:
                created_cards.append(response.json()["id"])
        
        return {
            "success": True,
            "message": f"Created {len(created_cards)} cards in Trello",
            "cards": created_cards
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Trello export failed: {str(e)}")

@app.post("/api/notify")
async def send_notifications(request: NotificationRequest, background_tasks: BackgroundTasks):
    """Send meeting summary via email and Slack"""
    
    # Format summary
    summary = f"""
    Meeting Summary - {datetime.now().strftime('%Y-%m-%d %H:%M')}
    
    {request.analysis.summary}
    
    TASKS ({len(request.analysis.tasks)}):
    """ + "\n".join([f"• {task.title} - {task.assignee} (Due: {task.due_date})" 
                      for task in request.analysis.tasks])
    
    summary += f"""
    
    DECISIONS ({len(request.analysis.decisions)}):
    """ + "\n".join([f"• {decision}" for decision in request.analysis.decisions])
    
    summary += f"""
    
    RISKS ({len(request.analysis.risks)}):
    """ + "\n".join([f"• {risk}" for risk in request.analysis.risks])
    
    # Send email
    if request.email and request.email.strip():  # Only send email if email is provided
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
            smtp_port = int(os.environ.get("SMTP_PORT", "587"))
            smtp_user = os.environ.get("SMTP_USER")
            smtp_password = os.environ.get("SMTP_PASSWORD")
            
            print(f"Email config - Server: {smtp_server}, Port: {smtp_port}, User: {smtp_user}")
            
            if smtp_user and smtp_password:
                msg = MIMEMultipart()
                msg['From'] = smtp_user
                msg['To'] = request.email
                msg['Subject'] = f"Meeting Summary - {datetime.now().strftime('%Y-%m-%d')}"
                
                msg.attach(MIMEText(summary, 'plain'))
                
                print(f"Attempting to send email to {request.email}...")
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                print("TLS started, attempting login...")
                server.login(smtp_user, smtp_password)
                print("Login successful, sending message...")
                server.send_message(msg)
                server.quit()
                print("Email sent successfully!")
            else:
                print("SMTP credentials not configured")
        except Exception as e:
            import traceback
            print(f"Email sending failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
    
    # Send Slack notification
    slack_webhook = request.slack_webhook
    print(f"Slack webhook from request: {slack_webhook}")
    
    # If 'use_env' is passed, use the webhook from environment
    if slack_webhook == 'use_env':
        slack_webhook = os.environ.get("SLACK_WEBHOOK_URL")
        print(f"Using Slack webhook from env: {slack_webhook[:50] if slack_webhook else 'NOT SET'}...")
    
    if slack_webhook:
        try:
            import requests
            
            print(f"Sending Slack notification to: {slack_webhook[:50]}...")
            
            slack_message = {
                "text": f"📝 *Meeting Summary*\n\n{request.analysis.summary}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": "📝 Meeting Summary"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": request.analysis.summary}
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Tasks:* {len(request.analysis.tasks)} | *Decisions:* {len(request.analysis.decisions)} | *Risks:* {len(request.analysis.risks)}"
                        }
                    }
                ]
            }
            
            response = requests.post(slack_webhook, json=slack_message)
            print(f"Slack response status: {response.status_code}")
            print(f"Slack response body: {response.text}")
            if response.status_code == 200:
                print("Slack message sent successfully!")
            else:
                print(f"Slack error: {response.text}")
        except Exception as e:
            import traceback
            print(f"Slack notification failed: {e}")
            print(f"Traceback: {traceback.format_exc()}")
    else:
        print("No Slack webhook configured or provided")
    
    return {
        "success": True,
        "message": "Notifications sent successfully"
    }

@app.get("/")
async def root():
    return {
        "message": "AI Meeting Notes Agent API",
        "version": "1.0.0",
        "endpoints": [
            "/api/analyze",
            "/api/export/jira",
            "/api/export/notion",
            "/api/notify"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)