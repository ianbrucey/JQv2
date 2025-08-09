# URL Routing and User Experience Flow

This document explains the complete user journey from authentication through container provisioning, including URL routing, domain strategy, and technical architecture for our multi-tenant legal case management system.

## User Journey Overview

```
justicequest.com (login) → justicequest.com/cases (selection) → justicequest.com/workspace/case-123 (container)
```

**Key Principle**: User stays on the same domain throughout the entire experience for simplicity and trust.

## Detailed User Experience Flow

### **Step 1: Initial Access and Authentication**
```
URL: https://justicequest.com
User sees: Landing page with login form
```

**User Action**: Enters credentials and clicks "Sign In"

**Backend Process**:
- Validate credentials against PostgreSQL user table
- Issue JWT token with user claims
- Redirect to case selection

### **Step 2: Case Selection Interface**
```
URL: https://justicequest.com/cases
User sees: List of their cases (no container running yet)
```

**Technical Details**:
- Static React interface served from main application
- Case list fetched via API: `GET /api/users/{user_id}/cases`
- No container provisioned yet - this is just metadata from PostgreSQL
- Fast loading (< 500ms) since it's just database queries

### **Step 3: Case Selection and Container Provisioning**
```
URL: https://justicequest.com/workspace/case-123
User sees: Loading screen "Preparing your workspace..."
```

**User Action**: Clicks on "Smith v. Jones" case

**URL Transition**:
```
Before: https://justicequest.com/cases
After:  https://justicequest.com/workspace/case-123
```

**Backend Process** (3-5 seconds):
1. Check if user has active container session
2. If not, provision new container
3. Fetch case files from object storage to workspace
4. Start OpenHands agent in container
5. Return workspace ready signal

### **Step 4: Active Workspace**
```
URL: https://justicequest.com/workspace/case-123
User sees: Full case workspace with file browser and AI assistant
```

**Technical Details**:
- Same domain, different React route
- WebSocket connection established for real-time agent communication
- File operations proxied through main application to user's container

## Technical Architecture: Single Domain Strategy

### **Recommended Approach: Unified Domain with Proxy Routing**

```
┌─────────────────────────────────────────────────────────────┐
│                    justicequest.com                         │
│                   (Load Balancer)                           │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                Main Application                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Frontend (React SPA)                               │   │
│  │  Routes:                                            │   │
│  │  - /login                                           │   │
│  │  - /cases                                           │   │
│  │  - /workspace/:caseId                               │   │
│  │  - /profile                                         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Backend API (FastAPI)                              │   │
│  │  - Authentication & user management                 │   │
│  │  - Case metadata operations                         │   │
│  │  - Container orchestration                          │   │
│  │  - Workspace proxy (routes to user containers)     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────┐
│                Container Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Container 1 │  │ Container 2 │  │ Container 3 │         │
│  │ (User A)    │  │ (User B)    │  │ (User C)    │         │
│  │ Port: 8001  │  │ Port: 8002  │  │ Port: 8003  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

### **Why Single Domain Strategy?**

**Benefits**:
- **User Trust**: No confusing domain changes or redirects
- **Simple SSL**: Single certificate for justicequest.com
- **Session Management**: Cookies and JWT tokens work seamlessly
- **SEO/Branding**: Consistent domain presence
- **Development**: Simpler CORS and authentication flows

**Alternative Approaches (Not Recommended)**:
- **Subdomains** (`app.justicequest.com`): Adds complexity, SSL cert management
- **User-specific subdomains** (`user123.justicequest.com`): DNS complexity, wildcard certs
- **Different domains**: Breaks user trust, complex authentication

## Routing Implementation Details

### **Frontend Routing (React Router)**

```typescript
// App.tsx
function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/cases" element={<CaseSelectionPage />} />
        <Route path="/workspace/:caseId" element={<WorkspacePage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Routes>
    </Router>
  );
}

// WorkspacePage.tsx
function WorkspacePage() {
  const { caseId } = useParams();
  const [containerStatus, setContainerStatus] = useState('provisioning');
  
  useEffect(() => {
    // Trigger container provisioning
    provisionWorkspace(caseId).then(() => {
      setContainerStatus('ready');
    });
  }, [caseId]);
  
  if (containerStatus === 'provisioning') {
    return <LoadingScreen message="Preparing your workspace..." />;
  }
  
  return <WorkspaceInterface caseId={caseId} />;
}
```

### **Backend Proxy Routing**

```python
# main.py (FastAPI)
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import httpx

app = FastAPI()

# Session tracking
active_sessions = {}  # user_id -> container_info

@app.post("/api/workspace/{case_id}/provision")
async def provision_workspace(case_id: str, user: User = Depends(get_current_user)):
    """Provision container and return session info."""
    
    # Check if user already has active session
    if user.id in active_sessions:
        session = active_sessions[user.id]
        return {"status": "ready", "session_id": session["session_id"]}
    
    # Provision new container
    session_info = await container_manager.provision_container(user.id, case_id)
    active_sessions[user.id] = session_info
    
    return {"status": "ready", "session_id": session_info["session_id"]}

@app.api_route("/api/workspace/{case_id}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_to_container(case_id: str, path: str, request: Request, user: User = Depends(get_current_user)):
    """Proxy workspace requests to user's container."""
    
    # Get user's container info
    session = active_sessions.get(user.id)
    if not session:
        raise HTTPException(404, "No active workspace session")
    
    # Proxy request to container
    container_url = f"http://localhost:{session['port']}/{path}"
    
    async with httpx.AsyncClient() as client:
        # Forward the request to the container
        response = await client.request(
            method=request.method,
            url=container_url,
            headers=dict(request.headers),
            content=await request.body()
        )
        
        # Stream response back to client
        return StreamingResponse(
            content=response.iter_bytes(),
            status_code=response.status_code,
            headers=dict(response.headers)
        )
```

### **Container Port Management**

```python
class ContainerManager:
    def __init__(self):
        self.port_pool = range(8001, 9000)  # Available ports
        self.allocated_ports = set()
    
    async def provision_container(self, user_id: str, case_id: str):
        """Provision container with unique port."""
        
        # Allocate port
        port = self.allocate_port()
        
        # Create container
        container = await docker_client.containers.run(
            image="legal-workspace:latest",
            name=f"legal-session-{user_id}-{int(time.time())}",
            ports={'3000/tcp': port},  # Map container port 3000 to host port
            volumes={
                f"/var/legal-workspaces/{user_id}": {"bind": "/opt/workspace", "mode": "rw"}
            },
            environment={
                "USER_ID": user_id,
                "CASE_ID": case_id
            },
            detach=True
        )
        
        # Wait for container to be ready
        await self.wait_for_container_ready(port)
        
        return {
            "session_id": f"sess_{user_id}_{int(time.time())}",
            "container_id": container.id,
            "port": port,
            "user_id": user_id,
            "case_id": case_id
        }
    
    def allocate_port(self) -> int:
        """Allocate next available port."""
        for port in self.port_pool:
            if port not in self.allocated_ports:
                self.allocated_ports.add(port)
                return port
        raise Exception("No available ports")
```

## Load Balancing and Scaling

### **Single Server Deployment**
```
Internet → Load Balancer → Main App (justicequest.com) → User Containers (ports 8001-8999)
```

### **Multi-Server Deployment**
```
Internet → Load Balancer → App Servers (sticky sessions) → User Containers
```

**Sticky Session Strategy**:
- Use JWT token or session cookie to route user to same app server
- Each app server manages its own container pool
- Database tracks which server hosts which user session

```python
# Load balancer configuration (nginx)
upstream app_servers {
    ip_hash;  # Sticky sessions based on client IP
    server app1.internal:8000;
    server app2.internal:8000;
    server app3.internal:8000;
}

server {
    listen 443 ssl;
    server_name justicequest.com;
    
    location / {
        proxy_pass http://app_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## User Experience Timeline

### **Complete URL and Visual Flow**

```
Time: 0s
URL:  https://justicequest.com
View: Landing page with login form

Time: 1s (after login)
URL:  https://justicequest.com/cases
View: Case selection interface (fast load from database)

Time: 2s (user clicks case)
URL:  https://justicequest.com/workspace/case-123
View: Loading screen "Preparing your workspace..."
      Progress indicator showing container provisioning

Time: 5s (container ready)
URL:  https://justicequest.com/workspace/case-123
View: Full workspace interface
      - File browser on left
      - AI assistant on right
      - Case files loaded and ready
```

### **Browser Address Bar States**

1. **Login**: `https://justicequest.com/login`
2. **Case Selection**: `https://justicequest.com/cases`
3. **Workspace Loading**: `https://justicequest.com/workspace/case-123` (loading spinner)
4. **Active Workspace**: `https://justicequest.com/workspace/case-123` (full interface)
5. **Case Switching**: `https://justicequest.com/workspace/case-456` (new case)

**Key Point**: URL changes reflect the user's intent and current context, but domain remains constant.

## Error Handling and Edge Cases

### **Container Provisioning Failures**
```
URL: https://justicequest.com/workspace/case-123
View: Error message "Unable to prepare workspace. Please try again."
Action: Retry button or redirect back to case selection
```

### **Session Timeouts**
```
URL: https://justicequest.com/workspace/case-123
View: "Session expired" modal with re-authentication
Action: Redirect to login, preserve intended case in URL params
```

### **Network Issues**
```
URL: https://justicequest.com/workspace/case-123
View: "Connection lost" banner with reconnection attempts
Action: Automatic retry with exponential backoff
```

This single-domain strategy provides a seamless user experience while maintaining technical simplicity and security isolation through the container layer.
