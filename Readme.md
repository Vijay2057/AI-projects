### How to create and activate venv?
```commandline
python -m venv venv-chatbot
venv-chatbot\Scripts\activate
```

### Create .env file in root level and it contains
```commandline
GEMINI_API_KEY
SECRET_KEY
DATABASE_URL
```


### How to run application?
```commandline
uvicorn app:app --reload 
```

### How to run streamlit app
```commandline
streamlit run streamlit-ui.py
```

### How to generate a secret key for JWT
#### Run the below command
```commandline
openssl rand -hex 32            # For Linux/Unix
[guid]::NewGuid().ToString()    # In windows power shell
```


## Postgres Docker Image
### How to run postgres docker image?
```commandline
docker run --name my-postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgres -d postgres
```

### How to enter into postgres docker container?
```commandline
docker exec -it my_postgres psql -U postgres
```

### Commands to check content in postgres
```commandline
CREATE DATABASE chatbot   # To create database
\l                        # To check list of databases
\c chatbot                # Change to chatbot db
\dt                       # List tables
\d users                  # Describe users table
\conninfo                 # Table info
\q                        # Exit psql
```

### New style of github code push
1. Go to your GitHub account → Settings → Developer settings → Personal access tokens → Tokens (classic).
For new token:
2. Generate a new token with repo permissions.
3. When pushing code, use this token instead of your password:
```commandline
git remote set-url origin https://<USERNAME>@github.com/<USERNAME>/<REPO>.git
```
4. When you push code, then, when prompted for a password, paste the token.



### Steps to learn:
```commandline
Stage 1
Simple Gemini Chatbot
        ↓
Stage 2
Conversation History with list
        ↓
Stage 3
Persistent Chat History
        ↓
Stage 4
Multiple Conversations / Chat Sessions
        ↓
Stage 5
Streaming Responses
        ↓
Stage 6
System Instructions / Prompt Engineering
        ↓
Stage 7
Tool Calling
        ↓
Stage 8
RAG
        ↓
Stage 9
Memory
        ↓
Stage 10
AI Agent
        ↓
Stage 11
Production-ready AI Backend
```


## How to use alembic?
#### step 1: Install alembic
```commandline
pip install alembic     
```

#### step 2: Initialize Alembic
```commandline
alembic init alembic 
```
1. Creates an alembic/ folder with migration scripts.
2. Creates alembic.ini configuration file.

#### Step 3: Configure DB URL
Open alembic.ini and set your database connection string:
```commandline
sqlalchemy.url = postgresql+psycopg2://user:password@localhost/dbname
```

##### Step 4: Link Alembic to Models
In alembic/env.py, import your SQLAlchemy Base and set:
```commandline
from myapp.models import Base
target_metadata = Base.metadata
```
##### Step 5: Create Migration Script
Generate a new migration:
```commandline
alembic revision --autogenerate -m "create users table"
```
#### Step 6: Review Migration
1. Open the generated file in alembic/versions/.
2. Check upgrade() and downgrade() functions to ensure correctness.

#### Step 5: Apply Migration
```commandline
alembic upgrade head
```

#### Step 6: Downgrade Migration
If needed, roll back: Reverts the last migration.
```commandline
alembic downgrade -1
```