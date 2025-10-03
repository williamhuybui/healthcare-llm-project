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
- 3) *“How much does it cost for me to see a doctor?”* → (user, plans)  (user.csv, plan.csv) => go to user table to get planid => go to plan table to get plan's oop_max_individual with planid

Logic: Since Huy Bui plan id = 1 => go to plan table to get plan_name = Blue Advantage Gold HMO Standard => open this plan pdf => from pdf need $30 for primary visit OR $60 for specialize visit OR no charge for PREVENTIVE/SCREENING/IMMUNIZATION

Answer: Huy Bui will pay $30 for primary visit OR $60 for specialize visit OR no charge for PREVENTIVE/SCREENING/IMMUNIZATION

- 4) *“What facilities in Houston accept my insurance?”* → (user, facility, plans)  (user.csv, facility.csv, plans_pdf) => go to user table to get planid => go to facility table to get all facility_name that have plan_id included in accepts_plan_ids 

Logic: Since Huy Bui plan id = 1 and city = Houston => go to facility table get all facility have location at houston, which is 501 and 502 => from those facilities filter out to keep those have plan_id = 1 in accepts_plan_ids => 501 and 502 have => get 501 and 502 facility name => Houston Methodist Hospital and Memorial Hermann - Texas Medical Center

Answer: Houston Methodist Hospital and Memorial Hermann - Texas Medical Center are nearby facilities and can accept Huy Bui plan

- 5) *“Can you find a doctor near me who speaks Vietnamese?”* → (user, facility, doctor)  (user.csv, facility.csv, doctor.csv) => go to user table to get city => go to faicility to get all facility_id has same city => go to doctor look for all doctor have same city in our same city facility list => look for doctor has "vi" in languages 

Logic: Since Huy Bui plan id = 1 and city = Houston => go to facility table get all facility have location at houston, which is 501 and 502 => go to doctor table to filter out doctor work at 501 and 502 => get doctor_id = 1001 and 1002, who work at 501 or 502 facility => filter out doctor and keep doctor have "vi" in their languages => 1001 has => get this id doctor name => doctor_name = Thao Le, MD

Answer: Huy Buy can meet doctor Thao Le, MD, who speaks Vietnamese and are working at facility near to Huy Buy's location

### Complex scenario queries
- 6) *“If I had a heart attack and my hospital bill was $100,000, what would my out-of-pocket cost be?”* → (user, plans)  (user.csv, plan.csv) => go to user_information to get plan_id => go to coverage look for coverage_id has same plan_id => look for service_category => look for coverage_limit => the money need to pay

- 7) *“Do I need a referral to see a specialist, and which facilities nearby allow that?”* → (plans, facility)  (plans_pdf, facility.csv)

Logic: Since Huy Bui plan id = 1 and city = Houston 

=> go to plan table to get plan_name matched plan_id = 1 => Blue Advantage Gold HMO Standard => open Blue Advantage Gold HMO Standard's pdf => at first page the book have a question "Do you need a referral to see a specialist? " => it answers "Yes" 


=> go to facility table get all facility have location at houston, which is 501 and 502 => from those facilities filter out to keep those have plan_id = 1 in accepts_plan_ids => 501 and 502 have => get 501 and 502 facility name => Houston Methodist Hospital and Memorial Hermann - Texas Medical Center accept HuyBui plan

*Answer: Huy Bui with Blue Advantage Gold HMO Standard's plan must have a referral to see a specialist, and Houston Methodist Hospital and Memorial Hermann - Texas Medical Center, which accept HuyBui plan, allow him to met a specialist with a referral*

- 8) *“What preventive care services are fully covered under my plan?”* → (plans)   (plans_pdf, plan.csv)

Logic: Since Huy Bui plan id = 1 and deductible_individual = 1500 => go to plan table to get plan_name matched plan_id = 1 => Blue Advantage Gold HMO Standard => open Blue Advantage Gold HMO Standard's pdf 

=> there is question "What is the overall deductible?" => answer "$0 at Indian Health Care Provider or with IHCP referral at non-IHCP; or $1,500 Individual/$3,000 Family" => your type is $1,500 Individual/$3,000 Family and not IHCP or non_IHCP

=> there is question "Are there services covered before you meet your deductible? " => answer "... See a list of covered preventive services at ... " => go to a website => it says "Most health plans must cover a set of preventive services — like shots and screening tests — at no cost to you. This includes plans available through the Health Insurance Marketplace®." => got next link for adults => list of 22 free preventive service for adults

*Answer: Huy Bui with Blue Advantage Gold HMO Standard's plan with type $1,500 Individual/$3,000 Family not IHCP or non_IHCP can get 22 preventive free services list below: ...*


- 9) *“Are there any annual limits for physical therapy visits?”* → (plans, doctor)  (plans_pdf, doctor.csv)

Logic: Since Huy Bui plan id = 1 => go to plan table to get plan_name matched plan_id = 1 => Blue Advantage Gold HMO Standard => open Blue Advantage Gold HMO Standard's pdf => go to page 8/8 see "Rehabilitation services (physical therapy) " => look for "Rehabilitation services" information => go to page 5/8 see "Separate 35-visit maximum per benefit period for Habilitation services and Rehabilitation services, including chiropractic care." => 35-visit maximum per benefit period => go to page one a period is "Coverage Period: 01/01/2025 – 12/31/2025 " => a period is a year => 35-visit maximum per benefit year

*Answer: Huy Bui with Blue Advantage Gold HMO Standard's plan can do physical therapy visits with 35-visit maximum per benefit year*


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