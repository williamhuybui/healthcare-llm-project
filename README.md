# Goal
The goal of this project is to build a healthcare-focused chatbot that provides accurate answers without hallucination.

# Features
- **Supports multiple formats** – works with both structured data (CSVs) and unstructured documents (PDFs).  
- **Cross-dataset integration** – combines information from different tables (user, facility, doctor, plan) to answer questions accurately.  
- **Complex query handling** – can follow multi-step logic across datasets to resolve more advanced healthcare questions.  

# Data Sources
### user
- `user_id (PK)`, `first_name`, `last_name`, `city`, `state`, `zip`, `lang_pref`, `plan_id (FK)`, `primary_doctor_id (nullable)`

### plan
- `plan_id (PK)`, `plan_name`, `plan_type`, `premium_monthly`, `deductible_individual`, `oop_max_individual`, `pdf_url`

### facility
- `facility_id (PK)`, `facility_name`, `npi`, `city`, `state`, `zip`, `phone`, `accepts_plan_ids`

### doctor
- `doctor_id (PK)`, `doctor_name`, `npi`, `specialty`, `facility_id (FK)` (assume 1 primary facility), `languages`, `phone`, `email`

### pdf
- *MyBlue Health Silver 405*  
- *MyBlue Health Gold 403*  
- *Blue Advantage Gold HMO Standard*  

# How It Works
The chatbot can answer a wide range of questions, from straightforward to complex, by pulling from one or more datasets.

### Single-source queries
Assumption: 
101,Huy,Bui,Houston,TX,77002,vn,plan_id = 1,primary_doctor_id = 1001, role = Patient

- 1) *“What is the deductible for my plan?”* → (plans) (plan.csv) 
Logic: Since Huy Bui plan id => deductible_individual = 1500 (plan)
Answer: The indivisual deductible for Huy Bui is 1500

- 2) *“Which doctors specialize in pediatrics?”* → (doctor)  (doctor.csv)
Logic: Since Huy Bui locate in Houston =>  grab facility 501,502 (facility) -> No doctor in pediatrics (doctor)
Answer: I could not find any doctor who specialized in pediatrics in your area

### Multi-source queries
- 3) *“How much does it cost for me to see a doctor?”* → (user, plans)  (user.csv, plan.csv)
- 4) *“What facilities in Houston accept my insurance?”* → (user, facility, plans)  (user.csv, facility.csv, plans_pdf)
- 5) *“Can you find a doctor near me who speaks Vietnamese?”* → (user, facility, doctor)  (user.csv, facility.csv, doctor.csv)

### Complex scenario queries
- 6) *“If I had a heart attack and my hospital bill was $100,000, what would my out-of-pocket cost be?”* → (user, plans)  (user.csv, plan.csv)
- 7) *“Do I need a referral to see a specialist, and which facilities nearby allow that?”* → (plans, facility)  (plans_pdf, facility.csv)
- 8) *“What preventive care services are fully covered under my plan?”* → (plans)   (plans_pdf, plan.csv)
- 9) *“Are there any annual limits for physical therapy visits?”* → (plans, doctor)  (plans_pdf, doctor.csv)

# User Story
### Step 1. User Sign-In
- The system authenticates the user.  
- `user.csv` provides user profile info (plan ID, language preference, location, etc.).  
- This context is attached to the chat session.  

### Step 2. Chat Start
- The user begins asking questions.  
- The request is passed into the orchestration layer.  

### Step 3. Planning Agent
- Analyzes the user’s question and identifies which data sources are relevant (`user.csv`, `facility.csv`, `doctor.csv`, `plans.pdf`).  
- Checks **feasibility**: does the system already have enough context to answer? 
   - If not, it can either (a) ask the user for more information, or (b) reframe the plan with fallback options.  
   - If it is, outputs a structured plan of action (roadmap) for the next agent.  

### Step 4. ReAct Agent
- A ReAct-style Agent executes the plan.  
- It uses the right tools: SQL queries for CSVs, semantic/vector search for PDFs

### Step 5. Validation Agent
- A Validate Agent checks the draft answer against:  
  - The retrieved sources (to ensure grounding)  
  - General domain knowledge (e.g., no contradictions to SBC rules)  
- If validation fails, control loops back to Step 3 for replanning.  

### Step 6. User Response
- The validated answer is returned to the user with citations and, if applicable, breakdowns of costs or reasoning steps.  