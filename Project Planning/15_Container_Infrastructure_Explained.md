# Container Infrastructure Explained (Non-DevOps Guide)

This document explains the container provisioning architecture in simple terms, focusing on where containers run, how resources are allocated, and why the process takes 3-5 seconds.

## 1. Server Architecture: Where Containers Run

### **Single Server Deployment (Recommended for Start)**

**Answer**: All containers run on the **same physical server** as the main web application.

```
Physical Server (32GB RAM, 8 CPU cores)
├── Main Web Application (justicequest.com)
│   ├── React Frontend
│   ├── FastAPI Backend  
│   ├── PostgreSQL Database
│   └── Redis Cache
├── User Container 1 (User A's workspace)
├── User Container 2 (User B's workspace)
├── User Container 3 (User C's workspace)
├── User Container 4 (User D's workspace)
└── User Container 5 (User E's workspace)
```

**Think of it like apartments in a building:**
- The building = your physical server
- Ground floor = main web application (lobby, management office)
- Floors 2-6 = individual user workspaces (apartments)
- Each apartment is isolated but shares the building's utilities (internet, power)

### **Why Same Server Initially?**

**Advantages:**
- **Simplicity**: Everything runs in one place, easier to manage
- **Cost**: No need for multiple servers initially
- **Speed**: No network delays between main app and containers
- **Development**: Easier to debug and monitor

**Limitations:**
- **Scale ceiling**: Limited by single server resources
- **Single point of failure**: If server goes down, everyone is affected

## 2. Container Lifecycle: The 3-5 Second Process

### **What Happens When User Clicks "Open Case"**

Let's trace exactly what happens during those 3-5 seconds:

#### **Second 1: Container Creation Request**
```
User clicks case → Main app receives request → Docker engine starts new container
```

**Technical Process:**
1. Main app calls Docker API: "Create new container for user_123"
2. Docker engine allocates resources (4GB RAM, 2 CPU cores)
3. Docker pulls container image from local cache (legal-workspace:latest)
4. Docker creates isolated filesystem space for the container

#### **Second 2-3: Container Startup**
```
Container boots → OpenHands agent initializes → Workspace directory mounted
```

**Technical Process:**
1. Container operating system starts (lightweight Linux)
2. OpenHands agent software launches inside container
3. Container gets assigned unique port (e.g., 8001)
4. Workspace directory mounted: `/var/legal-workspaces/user_123` → `/opt/workspace`

#### **Second 4-5: Case Data Loading**
```
Case files downloaded → Workspace populated → Container reports "ready"
```

**Technical Process:**
1. Container fetches case files from S3/Azure Blob storage
2. Files written to local workspace directory
3. File permissions and folder structure set up
4. Container sends "ready" signal to main application

### **Why 3-5 Seconds Specifically?**

**Time Breakdown:**
- **Container creation**: 1-2 seconds (allocating resources, starting OS)
- **Agent startup**: 1 second (launching OpenHands software)
- **File download**: 1-2 seconds (fetching case files from cloud storage)

**Factors affecting speed:**
- **Container image size**: Larger images take longer to start
- **Case file size**: More/larger files take longer to download
- **Server resources**: Busy server = slower startup
- **Network speed**: Slower internet = slower file downloads

## 3. Resource Allocation: 32GB Server Example

### **Resource Division (5 Concurrent Users)**

```
32GB RAM Server Allocation:
├── Operating System: 4GB
├── Main Web Application: 8GB
│   ├── React Frontend: 1GB
│   ├── FastAPI Backend: 2GB
│   ├── PostgreSQL Database: 4GB
│   └── Redis Cache: 1GB
├── User Containers: 20GB (4GB each × 5 users)
└── System Buffer: 0GB (tight but workable)
```

**CPU Allocation (8 cores):**
```
8 CPU Cores:
├── Main Application: 2 cores
├── Database: 2 cores  
├── User Containers: 4 cores (0.8 cores each × 5 users)
```

### **Physical vs Logical Separation**

**Physical Reality:**
- All processes run on the same physical server
- Same CPU, same RAM, same hard drive
- Containers share the server's resources

**Logical Isolation:**
- Each container thinks it has its own computer
- Container can't see other containers' files
- Container can't access other users' memory
- If one container crashes, others keep running

**Analogy**: Like having 5 virtual machines on one computer, but more efficient.

### **Scaling Beyond 5 Users**

**Option 1: Bigger Server**
```
64GB RAM Server:
├── Main Application: 8GB
├── User Containers: 50GB (4GB each × 12 users)
├── System: 6GB
```

**Option 2: Multiple Servers**
```
Server 1 (32GB): Main app + 5 user containers
Server 2 (32GB): 8 user containers only
Server 3 (32GB): 8 user containers only
Total capacity: 21 concurrent users
```

## 4. Network Architecture: How Everything Connects

### **Container Communication Paths**

#### **User Container → Main Web Application**
```
Container (port 8001) ← HTTP requests → Main App (port 8000)
```

**Example**: When user saves a file, container sends HTTP request to main app to update database.

**Technical Details:**
- Containers use "localhost" to reach main app (same server)
- Very fast communication (no internet involved)
- Main app authenticates all requests from containers

#### **Container → PostgreSQL Database**
```
Container → Main App → PostgreSQL Database
```

**Why not direct?**: Security. Containers don't get direct database access.

**Process**:
1. Container needs to save case metadata
2. Container sends request to main app
3. Main app validates request and updates database
4. Main app sends response back to container

#### **Container → Object Storage (S3/Azure)**
```
Container → Internet → S3/Azure Blob Storage
```

**Direct Access**: Containers can download/upload files directly to cloud storage.

**Security**: Main app gives containers temporary access tokens (1-hour expiry).

### **Network Diagram**

```
┌─────────────────────────────────────────────────────────────┐
│                    Physical Server                          │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Main Application                       │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │   │
│  │  │   React     │  │   FastAPI   │  │ PostgreSQL  │ │   │
│  │  │ Frontend    │  │  Backend    │  │ Database    │ │   │
│  │  │ Port: 3000  │  │ Port: 8000  │  │ Port: 5432  │ │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ Container 1 │  │ Container 2 │  │ Container 3 │         │
│  │ (User A)    │  │ (User B)    │  │ (User C)    │         │
│  │ Port: 8001  │  │ Port: 8002  │  │ Port: 8003  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Internet/Cloud  │
                    │ - S3 Storage    │
                    │ - External APIs │
                    └─────────────────┘
```

## Real-World Example: User Opens Case

### **Step-by-Step Resource Usage**

**Before User Action:**
```
Server State:
├── Main App: Running, using 8GB RAM
├── 2 other users already active: Using 8GB RAM
├── Available: 16GB RAM, 4 CPU cores
```

**User Clicks "Smith v. Jones Case":**

**Second 1:**
```
Docker creates container:
├── Allocates: 4GB RAM, 0.8 CPU cores
├── Remaining: 12GB RAM, 3.2 CPU cores
├── Container gets port 8003
```

**Second 2-3:**
```
Container starts OpenHands:
├── Downloads case files (50MB) from S3
├── Creates workspace folders
├── Initializes AI agent
```

**Second 4-5:**
```
Container reports ready:
├── User sees workspace interface
├── Files available for editing
├── AI assistant ready for commands
```

**Final Server State:**
```
Server Resources:
├── Main App: 8GB RAM
├── 3 active user containers: 12GB RAM  
├── Available: 12GB RAM (room for 3 more users)
```

## Key Takeaways

1. **Same Server**: All containers run on the same physical server as the main app
2. **Resource Sharing**: Containers share CPU and RAM but are isolated from each other
3. **Network**: Containers talk to main app via localhost, to cloud storage via internet
4. **Scaling**: Add more RAM/CPU to support more users, or add more servers
5. **Speed**: 3-5 seconds is normal for container startup + file download

This architecture provides strong isolation between users while keeping infrastructure simple and costs low for initial deployment.
