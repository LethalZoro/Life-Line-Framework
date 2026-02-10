
import os
import json
from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ValidationError
from typing import List, Optional
import io
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
import warnings
# from weasyprint import HTML, CSS

from schemas import SystemInput, SystemOutput

# Load environment variables
load_dotenv()

# Initialize API Key
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("WARNING: OPENAI_API_KEY not found. /api/analyze endpoint will fail.")

app = FastAPI(title="Beresfords Life-First Planner")

# Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup Templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("comprehensive_input.html", {"request": request})

@app.post("/api/analyze", response_model=SystemOutput)
async def analyze_life_plan(data: SystemInput):
    """
    The Core Logic Engine.
    Takes structured user input, injects specific Beresfords Doctrine + Dynamic Assumptions,
    and returns a valid JSON Life Plan.
    """
    
    # 1. Extract Dynamic Assumptions
    asm = data.assumptions
    
    if not api_key:
         raise HTTPException(status_code=500, detail="Server Error: OPENAI_API_KEY not configured in .env file.")

    # --- PRE-CALCULATIONS (Engineering Truth) ---
    # 1. Income Capital (Life Stages Multi-Layer)
    total_income_capital = 0
    income_details = []
    
    # We estimate Start Year = 2026.
    p1_current_age_est = 2026 - data.profile.partner1_dob.year # Approx
    
    for stage in data.lifestyle.life_stages:
        deferral = stage.start_age - p1_current_age_est
        if deferral < 0: deferral = 0 
        duration = stage.end_age - stage.start_age
        
        cap, _ = calculate_income_portfolio(
            start_year=2026, 
            duration_years=duration, 
            initial_drawdown=stage.annual_income, 
            inflation=asm.general_inflation / 100.0,
            income_return=0.045, growth_return=0.005, tax_rate=0.15, fee_rate=0.011,
            defer_years=deferral,
            p1_age=stage.start_age, 
            p2_age=stage.start_age 
        )
        total_income_capital += cap
        income_details.append(f"{stage.name}: ${cap:,.0f}")
    
    # 2. Car Capital
    total_car_capital = 0
    car_details = []
    for car in data.lifestyle.cars:
        cap, _ = calculate_asset_portfolio(
            start_year=2026,
            duration_years=30, # Life expectancy duration
            purchase_value=car.purchase_value,
            replacement_cycle=car.replacement_cycle,
            annual_holding_cost=car.holding_cost,
            trade_in_value=car.purchase_value * 0.2, 
            inflation=asm.general_inflation / 100.0,
            income_return=0.035, growth_return=0.045, tax_rate=0.15, fee_rate=0.011,
            p1_age=p1_current_age_est, p2_age=0
        )
        total_car_capital += cap
        car_details.append(f"{car.name}: ${cap:,.0f}")
        
    # 3. New Specific Assets (Boat, Caravan)
    total_toy_capital = 0
    toy_details = []
    
    toys = [("Boat", data.lifestyle.boat), ("Caravan", data.lifestyle.caravan)]
    for name, toy in toys:
        if toy and toy.purchase_value > 0:
            duration = toy.disposal_timing - toy.purchase_timing
            start_delay = toy.purchase_timing - p1_current_age_est
            if start_delay < 0: start_delay = 0
            
            cap, _ = calculate_asset_portfolio(
                start_year=2026 + start_delay,
                duration_years=duration,
                purchase_value=toy.purchase_value,
                replacement_cycle=0, # One off assumption
                annual_holding_cost=toy.holding_cost,
                trade_in_value=toy.disposal_value,
                inflation=asm.general_inflation / 100.0,
                income_return=0.035, growth_return=0.045, tax_rate=0.15, fee_rate=0.011,
                p1_age=toy.purchase_timing, p2_age=0,
                sell_at_end=True
            )
            # Discount back to 2026
            pv_factor = (1.06) ** -start_delay
            cap_pv = cap * pv_factor
            
            total_toy_capital += cap_pv
            toy_details.append(f"{name}: ${cap_pv:,.0f} (PV)")


    # 4. Holiday Capital (Granular)
    total_hol_capital = 0
    hol_details = []
    
    # Helper for Travel
    def process_travel(t_obj):
        if not t_obj: return 0, ""
        daily_sum = t_obj.cost_accom_daily + t_obj.cost_food_daily + t_obj.cost_fun_daily
        total_trip = (daily_sum * t_obj.duration_days) + (t_obj.flight_cost_per_person * 2)
        
        # Duration of habit
        dur = t_obj.end_age - t_obj.start_age
        delay = t_obj.start_age - p1_current_age_est
        if delay < 0: delay = 0
        
        # Calculate for that future block
        cap_fut, _ = calculate_holiday_portfolio(
            start_year=2026 + delay,
            duration_years=dur,
            daily_cost_total=total_trip,
            days_per_trip=1,
            trip_frequency_years=1,
            inflation=asm.general_inflation / 100.0,
            income_return=0.035, growth_return=0.045, tax_rate=0.15, fee_rate=0.011
        )
        # Discount PV
        pv = cap_fut * ((1.06) ** -delay)
        return pv, f"{t_obj.name}: ${pv:,.0f}"

    # List of travel buckets
    travel_buckets = [
        data.lifestyle.travel_domestic, 
        data.lifestyle.travel_international,
        data.lifestyle.travel_parents,
        data.lifestyle.travel_others
    ]
    
    for tb in travel_buckets:
        c, det = process_travel(tb)
        if c > 0:
            total_hol_capital += c
            hol_details.append(det)
            
    # 5. Medical & Buffers
    total_health_capital = 0
    if data.lifestyle.medical_expenses and data.lifestyle.medical_expenses.purchase_value > 0:
        # Treat as annual recurring like travel
        med = data.lifestyle.medical_expenses
        dur = med.disposal_timing - med.purchase_timing
        delay = med.purchase_timing - p1_current_age_est
        if delay < 0: delay = 0
        
        cap_fut, _ = calculate_holiday_portfolio(
            start_year=2026 + delay,
            duration_years=dur,
            daily_cost_total=med.purchase_value, # Annual cost
            days_per_trip=1, trip_frequency_years=1,
            inflation=asm.general_inflation / 100.0,
            income_return=0.045, growth_return=0.005, tax_rate=0.15, fee_rate=0.011 # Conservative for health
        )
        pv = cap_fut * ((1.05) ** -delay) # Lower discount for health
        total_health_capital += pv

    pre_calc_summary = f"""
    ### ENGINEERED FINANCIAL TRUTH (PRE-CALCULATED):
    - **Income Capital (Life Stages):** ${total_income_capital:,.2f}
      - Breakdown: {', '.join(income_details)}
    - **Transport Capital (Cars):** ${total_car_capital:,.2f}
    - **Toys & Lumpy Assets:** ${total_toy_capital:,.2f} ({', '.join(toy_details)})
    - **Travel Capital (All):** ${total_hol_capital:,.2f} ({', '.join(hol_details)})
    - **Health & Medical Capital:** ${total_health_capital:,.2f}
    
    - **Total Core Capital Needed:** ${(total_income_capital + total_car_capital + total_toy_capital + total_hol_capital + total_health_capital):,.2f}
    
    USE THESE EXACT NUMBERS in the 'Capital Requirements' section of the output. 
    """


    # --- MULTI-STEP REASONING PIPELINE ---

    # STEP 1: THE WHY (Context Analysis)
    async def run_life_theme_analysis(data: SystemInput) -> str:
        theme_prompt = f"""
        ### ANALYSIS PHASE 1: THE LIFE THEME ("THE WHY")
        
        Analyze the client's "True North" to extract their Core Drivers.
        
        **INPUTS:**
        - **Wants:** {', '.join(data.profile.wants)}
        - **Don't Wants:** {', '.join(data.profile.dont_wants)}
        - **Barriers:** {', '.join([f"{b.description} ({b.impact_percentage}%)" for b in data.profile.barriers])}
        - **Eulogies:** Partner ({data.profile.eulogy_partner}), Child ({data.profile.eulogy_child}), Friend ({data.profile.eulogy_friend})
        
        **OUTPUT REQUIREMENT:**
        Write a 1-paragraph "Life Theme" summary (approx 100 words).
        - Identify the *emotional conflict* (e.g. "Craves freedom but fears running out").
        - Identify the *ultimate definition of success* based on the eulogies.
        - This summary will be passed to the Strategist to design the financial solution.
        """
        
        llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7, api_key=api_key) # Use fast/smart model for reasoning
        # llm = ChatOpenAI(model="gpt-5.2-2025-12-11", temperature=0.7, api_key=api_key) # Using user's pref model
        
        msg = [SystemMessage(content="You are an empathetic expert human profiler."), HumanMessage(content=theme_prompt)]
        resp = llm.invoke(msg)
        return resp.content


    # STEP 3: THE HOW (Strategic Synthesis)
    system_prompt = f"""
### ROLE: THE BERESFORDS LIFE-FIRST STRATEGIST
"Map the life first, then engineer the money."
You are not a financial planner; you are a Life Architect.

### INPUT CONTEXT (FROM PHASE 1 & 2)
**LIFE THEME (The Why):**
{{life_theme}}

**ENGINEERED TRUTH (The Numbers):**
{pre_calc_summary}

### CORE DOCTRINE (THE LAWS)
1.  **Life > Money:** Money is a servant. It is not the goal.
2.  **The Two-Number Model:**
    *   **Number 1 (Dignity):** The cost to remain housed, fed, and safe.
    *   **Number 2 (Expression):** The cost to live fully (Travel, Toys, Generosity).
    *   **Freedom** lives in the space between.
3.  **Survivor Gap:** 
    *   There is ALWAYS a survivor gap. FUND IT. 
    *   Use the "Planning Allowance" (3-6 years) for the younger partner.
4.  **Capital Architecture:**
    *   **Bucket 1 (Stability):** Emergency + 2yr Income.
    *   **Bucket 2 (Momentum):** Active Lifestyle (Cars, Travel).
    *   **Bucket 3 (Growth):** Long-term Legacy & Aged Care.

### INSTRUCTIONS
1.  **Synthesize:** Combine the emotional "Life Theme" with the cold "Engineered Truth". 
    *   *Example:* "Your desire for 'Freedom' (Theme) is currently underfunded by $200k (Truth). We must adjust the Boat purchase..."
2.  **Gap Analysis:** If Starting Capital < Required Capital, be BRUTALLY HONEST but provide the trade-off.
3.  **Tables:** You MUST populate the `lifeline_register` with the exact items from the Engineered Truth.

### OUTPUT FORMAT
Strictly `SystemOutput` schema.
"""

    try:
        # EXECUTE PIPELINE
        
        # Step 1: Why
        life_theme = await run_life_theme_analysis(data)
        
        # Step 2: What (Done above in Pre-Calc)
        
        # Step 3: How (Synthesis)
        final_prompt = system_prompt.replace("{life_theme}", life_theme)
        
        # Using specific model version for stability
        llm = ChatOpenAI(model="gpt-5.2-2025-12-11", temperature=0.7, api_key=api_key)
        
        # Enforce Structured Output
        structured_llm = llm.with_structured_output(SystemOutput)
        
        # Invoke the chain
        messages = [
            SystemMessage(content=final_prompt),
            HumanMessage(content=f"Generate the Beresfords Life-First Plan based on the PROCESSED data below:\n\nUser JSON:\n{data.model_dump_json()}")
        ]
        
        result_parsed = structured_llm.invoke(messages)
        
        if not result_parsed:
             raise ValueError("Empty response from LLM")
            
        return result_parsed

    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# @app.post("/api/pdf")
# async def generate_pdf(
#     html_content: str = Body(...),
#     css_content: str = Body(...)
# ):
#     try:
#         # Create a PDF in memory
#         pdf_file = io.BytesIO()
        
#         # WeasyPrint conversion
#         html = HTML(string=html_content)
#         css = CSS(string=css_content)
#         html.write_pdf(target=pdf_file, stylesheets=[css])
        
#         pdf_file.seek(0)
        
#         return StreamingResponse(
#             pdf_file, 
#             media_type="application/pdf",
#             headers={"Content-Disposition": "attachment; filename=Beresfords_Life_Strategy.pdf"}
#         )
#     except Exception as e:
#         print(f"PDF Generation Error: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))

from langchain_core.tools import tool
from langchain.agents import create_agent
from calculations import calculate_income_portfolio, calculate_asset_portfolio, calculate_holiday_portfolio
from pydantic import BaseModel

# --- Define Tools for LangChain ---
@tool
def tool_income_portfolio(
    start_year: int, 
    duration_years: int, 
    income_needed: float, 
    p1_age: int,
    p2_age: int,
    defer_years: int = 0,
    portfolio_type: str = "Balanced",
    tax_rate: float = 0.15,
    fee_rate: float = 0.011,
    inflation: float = 0.03,
    name: str = "Income Portfolio"
):
    """
    Calculates detailed 'Income Portfolio' table (Necessary Life, Living Expenses).
    Inputs:
    - start_year: e.g. 2026
    - duration_years: e.g. 10 (Duration of DRAWDOWN phase).
    - defer_years: e.g. 10 (Duration of ACCUMULATION phase before drawdown).
      (Use defer_years > 0 for Stage 2/3 if funded from start).
    - income_needed: Net annual amount needed (e.g. 80000).
    - p1_age, p2_age: Ages at start year.
    - portfolio_type: "Conservative" or "Balanced".
    - name: e.g. "Stage 1", "Stage 2".
    """
    # 1. Map Portfolio Type to Returns
    if portfolio_type.lower() == "conservative":
        inc_ret = 0.045
        gr_ret = 0.005
    elif portfolio_type.lower() == "balanced":
        inc_ret = 0.035
        gr_ret = 0.045
    else:
        # Default to Balanced if unknown
        inc_ret = 0.035
        gr_ret = 0.045
        
    start_capital, data = calculate_income_portfolio(
        start_year=start_year,
        duration_years=duration_years,
        initial_drawdown=income_needed,
        inflation=inflation,
        income_return=inc_ret,
        growth_return=gr_ret,
        tax_rate=tax_rate,
        fee_rate=fee_rate,
        p1_age=p1_age,
        p2_age=p2_age,
        defer_years=defer_years
    )
    
    # 2. Format Table Output
    # Columns: Year | P1 Age | P2 Age | Open | Inc($) | Tax($) | Net Inc | Growth | Fees | Draw | Close
    table_rows = []
    header = "| Year | P1 Age | P2 Age | Open Bal | Inc Ret ($) | Tax ($) | Growth ($) | Fees ($) | Drawdown | Close Bal |"
    separator = "|---|---|---|---|---|---|---|---|---|---|"
    table_rows.append(header)
    table_rows.append(separator)
    
    for row in data:
        line = (
            f"| {row['Year']} "
            f"| {row['P1 Age']} "
            f"| {row['P2 Age']} "
            f"| ${row['Opening Balance']:,.0f} "
            f"| ${row['Income Return']:,.0f} "
            f"| ${row['Tax']:,.0f} "
            f"| ${row['Growth']:,.0f} "
            f"| ${row['Fees']:,.0f} "
            f"| ${row['Drawdown']:,.0f} "
            f"| ${row['Closing Balance']:,.0f} |"
        )
        table_rows.append(line)
        
    table_str = "\n".join(table_rows)
    
    summary = (
        f"### {name} ({portfolio_type}) - Stage Duration {duration_years}y (Defer: {defer_years}y)\n"
        f"**Required Starting Capital:** ${start_capital:,.0f}\n"
        f"**Parameters:** Inc Return {inc_ret*100:.2f}%, Growth {gr_ret*100:.2f}%, Tax {tax_rate*100:.2f}%, Fees {fee_rate*100:.2f}%, Inflation {inflation*100:.2f}%\n\n"
        f"{table_str}"
    )
    
    return summary


@tool
def tool_asset_portfolio(
    name: str, 
    start_year: int, 
    duration: int, 
    purchase: float, 
    replacement_cycle: int, 
    holding_cost: float, 
    trade_in: float, 
    p1_age: int,
    p2_age: int,
    portfolio_type: str = "Balanced",
    sell_at_end: bool = False,
    inflation: float = 0.03,
    tax_rate: float = 0.15,
    fee_rate: float = 0.011
):
    """
    Calculates detailed 'Asset Portfolio' table (Cars, Boats, etc).
    Use this for: **Cars, Boat, Caravan, Big Toys, or Lumpy Assets**.
    Inputs:
    - name: e.g. "Honda CRV", "Riviera Boat".
    - replacement_cycle: Years between new purchases (0 = One-off).
    - holding_cost: Annual costs (Rego, Insurance, Mooring, Maint).
    - trade_in: Value of old asset sold at replacement.
    - sell_at_end: If True, triggers a trade-in at plan end.
    """
    # 1. Map Portfolio Type
    if portfolio_type.lower() == "conservative":
        inc_ret = 0.045
        gr_ret = 0.005
    elif portfolio_type.lower() == "balanced":
        inc_ret = 0.035
        gr_ret = 0.045
    else:
        inc_ret = 0.035
        gr_ret = 0.045
        
    capital, data = calculate_asset_portfolio(
        start_year=start_year,
        duration_years=duration,
        purchase_value=purchase,
        replacement_cycle=replacement_cycle,
        annual_holding_cost=holding_cost,
        trade_in_value=trade_in,
        inflation=inflation,
        income_return=inc_ret,
        growth_return=gr_ret,
        tax_rate=tax_rate,
        fee_rate=fee_rate,
        p1_age=p1_age,
        p2_age=p2_age,
        sell_at_end=sell_at_end
    )
    
    # 2. Format Table Output
    table_rows = []
    # Headers matching the Excel roughly
    header = "| Year | P1 Age | P2 Age | Open Bal | Inc Ret | Tax | Growth | Purchase | Trade-In | Holding | Fees | Drawdown | Close Bal |"
    separator = "|---|---|---|---|---|---|---|---|---|---|---|---|---|"
    table_rows.append(header)
    table_rows.append(separator)
    
    for row in data:
        line = (
            f"| {row['Year']} "
            f"| {row['P1 Age']} "
            f"| {row['P2 Age']} "
            f"| ${row['Opening Balance']:,.0f} "
            f"| ${row['Income Return']:,.0f} "
            f"| ${row['Tax']:,.0f} "
            f"| ${row['Growth']:,.0f} "
            f"| ${row['Purchase Cost']:,.0f} "
            f"| ${row['Trade-In Value']:,.0f} "
            f"| ${row['Holding Cost']:,.0f} "
            f"| ${row['Fees']:,.0f} "
            f"| ${row['Drawdown']:,.0f} "
            f"| ${row['Closing Balance']:,.0f} |"
        )
        table_rows.append(line)
        
    table_str = "\n".join(table_rows)
    
    return (
        f"### Asset Portfolio ({name}) - {portfolio_type}\n"
        f"**Required Starting Capital:** ${capital:,.0f}\n"
        f"**Assumptions:** Inf {inflation*100:.2f}%, Inc {inc_ret*100:.2f}%, Growth {gr_ret*100:.2f}%, Sell at End: {sell_at_end}\n\n"
        f"{table_str}"
    )

@tool
def tool_holiday_portfolio(start_year: int, duration: int, total_trip_cost: float, frequency: int, inflation: float = 0.03):
    """
    Calculates capital for Holidays, Travel, or Recurring Lump Sums.
    Use this for: **Holidays, Overseas Trip, Medical Expenses, Renos**.
    Use 'frequency' to set how often it happens (1 = Annual).
    """
    capital, df = calculate_holiday_portfolio(
        start_year=start_year,
        duration_years=duration,
        daily_cost_total=total_trip_cost, # We pass the Total trip cost here for simplicity as 'daily_cost_total'
        days_per_trip=1, # Multiplier is 1 since we passed total
        trip_frequency_years=frequency,
        inflation=inflation,
        income_return=0.035, 
        growth_return=0.045,
        tax_rate=0.15,
        fee_rate=0.011
    )
    
    # Format Table Output
    table_rows = []
    header = "| Year | Open Bal | Inc Ret | Tax | Growth | Trip Cost | Fees | Drawdown | Close Bal |"
    separator = "|---|---|---|---|---|---|---|---|---|"
    table_rows.append(header)
    table_rows.append(separator)
    
    for row in df:
        line = (
            f"| {row['Year']} "
            f"| ${row['Opening Balance']:,.0f} "
            f"| ${row['Income Return']:,.0f} "
            f"| ${row['Tax']:,.0f} "
            f"| ${row['Growth']:,.0f} "
            # Holidays have 'Drawdown' as the trip cost if it's a trip year
            f"| ${row['Drawdown']:,.0f} " 
            f"| ${row['Fees']:,.0f} "
            f"| ${row['Drawdown']:,.0f} "
            f"| ${row['Closing Balance']:,.0f} |"
        )
        table_rows.append(line)
        
    table_str = "\n".join(table_rows)

    return (
        f"### Holiday Portfolio (Travel) - Balanced\n"
        f"**Required Starting Capital:** ${capital:,.0f}\n"
        f"**Parameters:** Freq {frequency}y, Cost ${total_trip_cost:,.0f}, Inf {inflation*100:.2f}%\n\n"
        f"{table_str}"
    )

@tool
def tool_project_age(current_age: int, start_year: int, target_age: int):
    """
    Calculates the Duration and End Year to reach a Target Age.
    Use this when user says "Until Age 90" or "Until Age 100".
    """
    duration = target_age - current_age
    end_year = start_year + duration
    return f"To reach Age {target_age} from Age {current_age} (starting {start_year}): Duration = {duration} years. End Year = {end_year}."

@tool
def tool_calculator(expression: str):
    """
    Evaluates a mathematical expression.
    Use this for basic arithmetic like adding durations or calculating deferral periods.
    e.g. "10 + 15", "2051 - 2026".
    """
    try:
        # Safe eval
        allowed_chars = "0123456789+-*/(). "
        if any(c not in allowed_chars for c in expression):
            return "Error: Invalid characters in expression."
        result = eval(expression, {"__builtins__": None}, {})
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

# --- Chat Request Model ---
class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

# --- Agent Helpers ---
tools = [tool_income_portfolio, tool_asset_portfolio, tool_holiday_portfolio, tool_project_age, tool_calculator]

# Global Checkpointer (In-Memory for now)
from langgraph.checkpoint.memory import MemorySaver
memory_saver = MemorySaver()

def get_agent_graph():
    if not api_key:
        raise ValueError("OpenAI API Key missing")
        
    llm = ChatOpenAI(model="gpt-5.2-2025-12-11", temperature=0, api_key=api_key)
    
    system_prompt = (
        "You are the Beresfords Life Planner Assistant. You have access to precise financial calculation tools.\n"
        "1. **Always use tools** to calculate numbers. Do not guess.\n"
        "2. **Age & Date Math**: Use `tool_project_age` to solve 'Until Age X' queries. Use `tool_calculator` for adding durations (e.g. Stage 3 Deferral = Stage 1 + Stage 2 durations).\n"
        "3. **Ask Questions**: If the user's request is vague, ask for the missing details properly.\n"
        "4. **Table Output**: ALWAYS display the full table returned by the tool.\n"
        "5. **Multi-Stage Income**: If user mentions 'Stage 2/3', calculate the `defer_years` accurately using the durations of identifying previous stages.\n"
        "6. **Asset Logic**: If user implies selling the asset at the end, use 'sell_at_end=True'.\n"
        "Assume Start Year is 2026 unless specified."
    )
    
    # create_agent returns a CompiledGraph
    graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        checkpointer=memory_saver
    )
    return graph

# --- Routes ---

@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

@app.post("/api/chat_message")
async def chat_message_endpoint(req: ChatRequest):
    try:
        graph = get_agent_graph()
        
        # Use provided thread_id or default to a generic one (but treating generic as shared is risky)
        # Ideally, frontend generates a UUID on load.
        thread_id = req.thread_id or "default_session"
        config = {"configurable": {"thread_id": thread_id}}
        
        # Input: list of messages
        inputs = {"messages": [{"role": "user", "content": req.message}]}
        final_state = graph.invoke(inputs, config=config)
        
        # Output: state dict with 'messages'
        messages = final_state.get("messages", [])
        if messages:
            last_msg = messages[-1]
            return {"response": last_msg.content}
        else:
            return {"response": "No response generated."}
            
    except Exception as e:
        print(f"Chat Error: {e}")
        return {"response": f"Error: {str(e)}"}

# --- Comprehensive Planner Routes ---

# --- Comprehensive Planner Routes & Logic ---

class CompProfile(BaseModel):
    p1_name: str
    p1_dob: str
    p2_name: str
    p2_dob: str
    children: List[dict] = []  # [{"name": "Emily", "dob": "2010-05-15"}, ...]

class CompAssumptions(BaseModel):
    income_return: float
    growth_return: float
    tax_rate: float
    inflation: float
    fee_load: float
    tax_free_age: Optional[int] = None  # Age after which tax drops to 0%

class CompItem(BaseModel):
    name: str
    income: Optional[float] = 0
    start: Optional[int] = 0
    end: Optional[int] = 0
    cost: Optional[float] = 0
    cycle: Optional[int] = 0
    holding: Optional[float] = 0
    resale: Optional[float] = 0
    tradein: Optional[float] = 0  # Trade-in value for cars/assets
    type: Optional[str] = None
    funding_start: Optional[int] = None # Age to start funding (if different from start age)
    apply_inflation: Optional[bool] = True
    portfolio: Optional[str] = None  # "conservative"/"balanced"/"growth"/None=auto
    # Per-item overrides (None = use global assumption)
    income_return: Optional[float] = None
    growth_return: Optional[float] = None
    tax_rate: Optional[float] = None
    fee_load: Optional[float] = None

class CompInput(BaseModel):
    profile: CompProfile
    assumptions: CompAssumptions
    incomes: List[CompItem]
    cars: List[CompItem]
    assets: List[CompItem]
    travel: List[CompItem]
    medical: dict
    universal_fund_age: Optional[int] = None

# --- Portfolio Presets ---
PORTFOLIO_PRESETS = {
    "conservative": {"income_return": 4.5, "growth_return": 0.5},
    "balanced":     {"income_return": 3.5, "growth_return": 4.5},
    "growth":       {"income_return": 2.5, "growth_return": 6.5},
}

def resolve_item_returns(item, global_asm: CompAssumptions, duration: int):
    """Resolve income_return, growth_return, tax_rate, fee_load for an item.
    Priority: item-level override > item.portfolio preset > auto-default by duration > global assumptions.
    Auto-default: >15yr=growth, 5-15yr=balanced, <5yr=conservative
    """
    ir = global_asm.income_return
    gr = global_asm.growth_return
    tax = global_asm.tax_rate
    fee = global_asm.fee_load

    # Determine portfolio
    portfolio = getattr(item, 'portfolio', None) if hasattr(item, 'portfolio') else None
    if not portfolio:
        if duration > 14:
            portfolio = "growth"
        elif duration >= 6:
            portfolio = "balanced"
        else:
            portfolio = "conservative"

    if portfolio in PORTFOLIO_PRESETS:
        ir = PORTFOLIO_PRESETS[portfolio]["income_return"]
        gr = PORTFOLIO_PRESETS[portfolio]["growth_return"]

    # Per-item overrides take highest priority
    item_ir = getattr(item, 'income_return', None) if hasattr(item, 'income_return') else None
    item_gr = getattr(item, 'growth_return', None) if hasattr(item, 'growth_return') else None
    item_tax = getattr(item, 'tax_rate', None) if hasattr(item, 'tax_rate') else None
    item_fee = getattr(item, 'fee_load', None) if hasattr(item, 'fee_load') else None
    
    if item_ir is not None: ir = item_ir
    if item_gr is not None: gr = item_gr
    if item_tax is not None: tax = item_tax
    if item_fee is not None: fee = item_fee

    return ir, gr, tax, fee, portfolio

def process_scenario(data: CompInput):
    """
    Central logic to process the CompInput scenario and return results + total capital.
    Now supports: per-item portfolio, inflate-from-current-age, universal fund age, child ages.
    """
    # 1. Parse Profile & Ages
    p1_birth_year = int(data.profile.p1_dob.split("-")[0]) 
    p2_birth_year = int(data.profile.p2_dob.split("-")[0]) if data.profile.p2_dob else p1_birth_year
    current_year = 2026
    p1_current_age = current_year - p1_birth_year
    p2_current_age = current_year - p2_birth_year
    
    # Parse children info
    children_info = []
    for child in data.profile.children:
        child_birth_year = int(child.get("dob", "2000-01-01").split("-")[0])
        children_info.append({
            "name": child.get("name", "Child"),
            "birth_year": child_birth_year,
            "current_age": current_year - child_birth_year
        })
    
    results = []
    asm = data.assumptions
    
    # Helper: Resolve fund_age — universal overrides individual
    def get_fund_age(item_funding_start):
        # Universal fund age takes priority when set
        if data.universal_fund_age is not None:
            return data.universal_fund_age
        if item_funding_start is not None:
            return item_funding_start
        return p1_current_age

    # Helper: Build per-year tax schedule that drops to 0% after tax_free_age
    def build_tax_schedule(tax_pct, p1_start_age, total_years):
        """Returns a list of per-year tax rates (as decimals).
        If tax_free_age is set, years where P1 age >= tax_free_age get 0% tax.
        If tax_free_age is None, returns the flat rate for every year."""
        rate = tax_pct / 100
        if asm.tax_free_age is None:
            return rate  # Return scalar — backwards compatible
        schedule = []
        for yr in range(total_years):
            age_this_year = p1_start_age + yr
            if age_this_year >= asm.tax_free_age:
                schedule.append(0.0)
            else:
                schedule.append(rate)
        return schedule
    
    # Helper for Chart Data - includes children ages
    def make_chart_data(df):
        labels = []
        for d in df:
            lbl = str(d['Year'])
            if 'P1 Age' in d and 'P2 Age' in d:
                lbl += f" ({d['P1 Age']}/{d['P2 Age']})"
            labels.append(lbl)
            
        return {
            "labels": labels,
            "balance": [d['Closing Balance'] for d in df],
            "drawdown": [d['Drawdown'] for d in df],
            "table_data": df,
            "children": children_info
        }

    # Helper: Prepend zero-balance rows from current_age to fund_age so graphs start from today
    def prepend_prefunding_rows(df_list, fund_age_local):
        """Prepend rows with $0 balance for years before funding starts."""
        if fund_age_local <= p1_current_age:
            return df_list
        prefix = []
        p2_base = p2_current_age if p2_current_age else p1_current_age
        for i in range(fund_age_local - p1_current_age):
            yr = current_year + i
            prefix.append({
                'Year': yr, 'P1 Age': p1_current_age + i, 'P2 Age': p2_base + i,
                'Opening Balance': 0, 'Income Return': 0, 'Tax': 0,
                'Income Net': 0, 'Growth': 0, 'Fees': 0,
                'Drawdown': 0, 'Closing Balance': 0
            })
        return prefix + df_list

    # Helper: PV discount capital from fund_age back to today
    def pv_to_today(cap_at_fund_age, growth_pct, fund_age_local):
        """Discount capital from fund_age to present value at current age."""
        years_back = fund_age_local - p1_current_age
        if years_back > 0:
            return cap_at_fund_age / ((1 + growth_pct / 100) ** years_back)
        return cap_at_fund_age

    # --- Process Incomes (Stages) ---
    for item in data.incomes:
        duration = item.end - item.start
        
        # Resolve per-item portfolio returns
        ir, gr, tax, fee, portfolio = resolve_item_returns(item, asm, duration)
        
        # Funding logic: start projection from fund_age
        fund_age = get_fund_age(item.funding_start)
        if fund_age < p1_current_age: fund_age = p1_current_age
        fund_year = current_year + (fund_age - p1_current_age)
        
        # Inflate income from current age to usage age
        years_to_inflate = item.start - p1_current_age
        if years_to_inflate > 0:
            inflated_income = item.income * ((1 + asm.inflation/100) ** years_to_inflate)
        else:
            inflated_income = item.income
        
        # Deferral from fund_age to start_age (capital grows, no drawdown)
        deferral_years = item.start - fund_age
        if deferral_years < 0: deferral_years = 0
        
        total_years_inc = deferral_years + duration
        tax_sched = build_tax_schedule(tax, fund_age, total_years_inc)
        
        cap, df_list = calculate_income_portfolio(
            start_year=fund_year,
            duration_years=duration,
            initial_drawdown=inflated_income,
            inflation=asm.inflation / 100,
            income_return=ir / 100,
            growth_return=gr / 100,
            tax_rate=tax_sched,
            fee_rate=fee / 100,
            p1_age=fund_age, 
            p2_age=p2_current_age + (fund_age - p1_current_age),
            defer_years=deferral_years
        )
        
        # Prepend zero rows so graph starts from current age
        df_list = prepend_prefunding_rows(df_list, fund_age)
        
        # PV discount to today for total capital calculation
        pv = pv_to_today(cap, gr, fund_age)
        
        # Build details string
        if years_to_inflate > 0:
            details = f"${item.income:,.0f}/yr today → ${inflated_income:,.0f}/yr inflated. Start Age {item.start}. Fund Age {fund_age}"
        else:
            details = f"${item.income:,.0f}/yr (Start Age {item.start}). Fund Age {fund_age}"
        
        results.append({
            "title": f"Income Stream: {item.name}",
            "capital_required": pv,
            "capital_at_fund_age": cap,
            "fund_age": fund_age,
            "chart_data": make_chart_data(df_list),
            "details": details,
            "portfolio_used": portfolio,
            "item_returns": {"income_return": ir, "growth_return": gr, "tax_rate": tax, "fee_load": fee}
        })

    # --- Process Cars ---
    for item in data.cars:
        duration = 30  
        
        # Resolve per-item portfolio returns
        ir, gr, tax, fee, portfolio = resolve_item_returns(item, asm, duration)
        
        # Funding Logic: start projection from fund_age
        fund_age = get_fund_age(item.funding_start)
        if fund_age < p1_current_age: fund_age = p1_current_age
        fund_year = current_year + (fund_age - p1_current_age)
        
        # Inflation Logic
        eff_inflation = (asm.inflation / 100) if item.apply_inflation else 0.0
        
        # Inflate cost from current age to usage age
        years_to_inflate = item.start - p1_current_age
        if years_to_inflate > 0:
            inflated_cost = item.cost * ((1 + asm.inflation/100) ** years_to_inflate)
        else:
            inflated_cost = item.cost
        
        # Use tradein if provided, else 30% of inflated cost
        tradein_val = item.tradein if item.tradein else inflated_cost * 0.3
        
        # Deferral from fund_age to item start
        defer_years_car = item.start - fund_age
        if defer_years_car < 0: defer_years_car = 0
        
        total_years_car = defer_years_car + duration
        car_tax_sched = build_tax_schedule(tax, fund_age, total_years_car)
        
        cap, df_list = calculate_asset_portfolio(
            start_year=fund_year,
            duration_years=duration,
            purchase_value=inflated_cost,
            replacement_cycle=item.cycle,
            annual_holding_cost=item.holding,
            trade_in_value=tradein_val, 
            inflation=eff_inflation,
            income_return=ir / 100,
            growth_return=gr / 100,
            tax_rate=car_tax_sched,
            fee_rate=fee / 100,
            p1_age=fund_age,
            p2_age=p2_current_age + (fund_age - p1_current_age),
            defer_years=defer_years_car
        )
        
        # Prepend zero rows so graph starts from current age
        df_list = prepend_prefunding_rows(df_list, fund_age)
        
        # PV discount to today
        pv = pv_to_today(cap, gr, fund_age)

        if years_to_inflate > 0:
            cost_detail = f"${item.cost:,.0f} today → ${inflated_cost:,.0f} inflated"
        else:
            cost_detail = f"${item.cost:,.0f}"
        
        results.append({
            "title": f"Vehicle: {item.name}",
            "capital_required": pv,
            "capital_at_fund_age": cap,
            "fund_age": fund_age,
            "chart_data": make_chart_data(df_list),
            "details": f"Cost {cost_detail}/{item.cycle}y. Fund Age {fund_age}. Inflation: {item.apply_inflation}",
            "portfolio_used": portfolio,
            "item_returns": {"income_return": ir, "growth_return": gr, "tax_rate": tax, "fee_load": fee}
        })

    # --- Process Assets (Toys) ---
    for item in data.assets:
        duration = item.end - item.start
        
        # Resolve per-item portfolio returns
        ir, gr, tax, fee, portfolio = resolve_item_returns(item, asm, duration)
        
        fund_age = get_fund_age(item.funding_start)
        if fund_age < p1_current_age: fund_age = p1_current_age
        fund_year = current_year + (fund_age - p1_current_age)
        eff_inflation = (asm.inflation / 100) if item.apply_inflation else 0.0
        
        # Inflate cost from current age to usage age
        years_to_inflate = item.start - p1_current_age
        if years_to_inflate > 0:
            inflated_cost = item.cost * ((1 + asm.inflation/100) ** years_to_inflate)
        else:
            inflated_cost = item.cost
        
        # Deferral from fund_age to item start
        defer_years_asset = item.start - fund_age
        if defer_years_asset < 0: defer_years_asset = 0
        
        total_years_asset = defer_years_asset + duration
        asset_tax_sched = build_tax_schedule(tax, fund_age, total_years_asset)
        
        cap, df_list = calculate_asset_portfolio(
             start_year=fund_year,
             duration_years=duration,
             purchase_value=inflated_cost,
             replacement_cycle=0, 
             annual_holding_cost=item.holding,
             trade_in_value=item.resale,
             inflation=eff_inflation,
             income_return=ir / 100,
             growth_return=gr / 100,
             tax_rate=asset_tax_sched,
             fee_rate=fee / 100,
             p1_age=fund_age,
             p2_age=p2_current_age + (fund_age - p1_current_age),
             sell_at_end=True,
             defer_years=defer_years_asset
        )
        
        # Prepend zero rows so graph starts from current age
        df_list = prepend_prefunding_rows(df_list, fund_age)
        
        # PV discount to today
        pv = pv_to_today(cap, gr, fund_age)

        if years_to_inflate > 0:
            cost_detail = f"${item.cost:,.0f} today → ${inflated_cost:,.0f} inflated"
        else:
            cost_detail = f"${item.cost:,.0f}"

        results.append({
            "title": f"Asset: {item.name}",
            "capital_required": pv,
            "capital_at_fund_age": cap,
            "fund_age": fund_age,
            "chart_data": make_chart_data(df_list),
            "details": f"Buy {cost_detail} @ Age {item.start}. Fund Age {fund_age}. Inf: {item.apply_inflation}",
            "portfolio_used": portfolio,
            "item_returns": {"income_return": ir, "growth_return": gr, "tax_rate": tax, "fee_load": fee}
        })

    # --- Process Travel ---
    for item in data.travel:
        duration = item.end - item.start
        if duration <= 0: continue
        
        # Resolve per-item portfolio returns
        ir, gr, tax, fee, portfolio = resolve_item_returns(item, asm, duration)
        
        fund_age = get_fund_age(item.funding_start)
        if fund_age < p1_current_age: fund_age = p1_current_age
        fund_year = current_year + (fund_age - p1_current_age)
        
        # Inflate cost from current age to usage age
        years_to_inflate = item.start - p1_current_age
        if years_to_inflate > 0:
            inflated_cost = item.cost * ((1 + asm.inflation/100) ** years_to_inflate)
        else:
            inflated_cost = item.cost
        
        # Deferral from fund_age to item start
        defer_years_travel = item.start - fund_age
        if defer_years_travel < 0: defer_years_travel = 0
        
        total_years_travel = defer_years_travel + duration
        travel_tax_sched = build_tax_schedule(tax, fund_age, total_years_travel)
        
        cap, df_list = calculate_holiday_portfolio(
            start_year=fund_year,
            duration_years=duration,
            daily_cost_total=inflated_cost,
            days_per_trip=1,
            trip_frequency_years=1,
            inflation=asm.inflation / 100,
            income_return=ir / 100,
            growth_return=gr / 100,
            tax_rate=travel_tax_sched,
            fee_rate=fee / 100,
            defer_years=defer_years_travel,
            p1_age=fund_age,
            p2_age=p2_current_age + (fund_age - p1_current_age)
        )
        
        # Prepend zero rows so graph starts from current age
        df_list = prepend_prefunding_rows(df_list, fund_age)
        
        # PV discount to today
        pv = pv_to_today(cap, gr, fund_age)

        if years_to_inflate > 0:
            cost_detail = f"${item.cost:,.0f}/yr today → ${inflated_cost:,.0f}/yr inflated"
        else:
            cost_detail = f"${item.cost:,.0f}/yr"

        results.append({
            "title": f"Travel: {item.name}",
            "capital_required": pv,
            "capital_at_fund_age": cap,
            "fund_age": fund_age,
            "chart_data": make_chart_data(df_list),
            "details": f"{cost_detail} from Age {item.start}. Fund Age {fund_age}.",
            "portfolio_used": portfolio,
            "item_returns": {"income_return": ir, "growth_return": gr, "tax_rate": tax, "fee_load": fee}
        })

    # --- Process Medical ---
    med = data.medical
    med_cost = float(med.get('cost', 0))
    if med_cost > 0:
        start = int(med.get('start', 70))
        end = int(med.get('end', 100))
        duration = end - start
        
        # Medical uses the same portfolio logic
        med_portfolio = med.get('portfolio', None)
        if not med_portfolio:
            if duration > 15: med_portfolio = "growth"
            elif duration >= 5: med_portfolio = "balanced"
            else: med_portfolio = "conservative"
        
        med_ir = asm.income_return
        med_gr = asm.growth_return
        med_tax = asm.tax_rate
        med_fee = asm.fee_load
        if med_portfolio in PORTFOLIO_PRESETS:
            med_ir = PORTFOLIO_PRESETS[med_portfolio]["income_return"]
            med_gr = PORTFOLIO_PRESETS[med_portfolio]["growth_return"]
        # Allow per-item overrides from medical dict
        if med.get('income_return'): med_ir = float(med['income_return'])
        if med.get('growth_return'): med_gr = float(med['growth_return'])
        if med.get('tax_rate') is not None: med_tax = float(med['tax_rate'])
        if med.get('fee_load'): med_fee = float(med['fee_load'])
        
        fund_age = int(med.get('funding_start', get_fund_age(None)))
        if fund_age < p1_current_age: fund_age = p1_current_age
        fund_year = current_year + (fund_age - p1_current_age)
        
        # Inflate medical cost from current age to usage age
        years_to_inflate = start - p1_current_age
        if years_to_inflate > 0:
            inflated_med = med_cost * ((1 + asm.inflation/100) ** years_to_inflate)
        else:
            inflated_med = med_cost
        
        # Deferral from fund_age to medical start
        defer_years_med = start - fund_age
        if defer_years_med < 0: defer_years_med = 0
        
        total_years_med = defer_years_med + duration
        med_tax_sched = build_tax_schedule(med_tax, fund_age, total_years_med)
        
        cap, df_list = calculate_holiday_portfolio(
            start_year=fund_year,
            duration_years=duration,
            daily_cost_total=inflated_med,
            days_per_trip=1,
            trip_frequency_years=1,
            inflation=asm.inflation / 100,
            income_return=med_ir / 100, 
            growth_return=med_gr / 100,
            tax_rate=med_tax_sched,
            fee_rate=med_fee / 100,
            defer_years=defer_years_med,
            p1_age=fund_age,
            p2_age=p2_current_age + (fund_age - p1_current_age)
        )
        
        # Prepend zero rows so graph starts from current age
        df_list = prepend_prefunding_rows(df_list, fund_age)
        
        # PV discount to today
        pv = pv_to_today(cap, med_gr, fund_age)
        
        if years_to_inflate > 0:
            cost_detail = f"${med_cost:,.0f}/yr today → ${inflated_med:,.0f}/yr inflated"
        else:
            cost_detail = f"${med_cost:,.0f}/yr"
             
        results.append({
            "title": "Medical Buffer",
            "capital_required": pv,
            "capital_at_fund_age": cap,
            "fund_age": fund_age,
            "chart_data": make_chart_data(df_list),
            "details": f"{cost_detail} from Age {start}. Fund Age {fund_age}.",
            "portfolio_used": med_portfolio,
            "item_returns": {"income_return": med_ir, "growth_return": med_gr, "tax_rate": med_tax, "fee_load": med_fee}
        })

    total_capital = sum(r['capital_required'] for r in results)
    
    return results, total_capital


@app.get("/comprehensive", response_class=HTMLResponse)
async def comp_page(request: Request):
    return templates.TemplateResponse("comprehensive_input.html", {"request": request})

@app.post("/api/generate_comprehensive_report", response_class=HTMLResponse)
async def generate_comp_report(request: Request, data: CompInput, display_mode: str = "charts"):
    results, total_capital = process_scenario(data)
    
    return templates.TemplateResponse("report_view.html", {
        "request": request, 
        "results": results, 
        "total_capital": total_capital,
        "profile": data.profile.model_dump(),
        "scenario_json": data.model_dump_json(), # Pass full state to frontend for interactive chat
        "display_mode": display_mode  # Pass the display mode choice
    })

# --- Interactive Chat Endpoint ---
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class ChatInteractiveRequest(BaseModel):
    message: str
    scenario: CompInput
    chat_history: List[ChatMessage] = []

@app.post("/api/chat_interactive")
async def chat_interactive(req: ChatInteractiveRequest):
    """
    Stateful interactive chat with memory.
    - Receives full chat history from the frontend
    - Builds LLM context from history + current scenario
    - Executes actions and returns updated state
    """
    
    current_scenario = req.scenario.model_copy(deep=True)
    scenario_json = current_scenario.model_dump_json(indent=2)

    system_prompt = f"""You are an expert Financial Planner AI assistant embedded in an interactive financial planning tool.
You have DEEP expertise in investment strategy, retirement planning, tax optimization, and portfolio management.

═══════════════════════════════════════════
CURRENT CLIENT SCENARIO (Live State):
═══════════════════════════════════════════
{scenario_json}

═══════════════════════════════════════════
YOUR CAPABILITIES:
═══════════════════════════════════════════

1. ANSWER QUESTIONS intelligently about the plan:
   - Explain how capital requirements are calculated
   - Analyze the impact of changes before making them
   - Compare different strategies and recommend the best approach
   - Explain tax implications, inflation effects, and portfolio choices
   - Calculate and explain compound growth scenarios
   - Discuss the trade-offs between conservative vs growth portfolios

2. MODIFY THE PLAN precisely using structured JSON actions (see below)

3. PROVIDE PROACTIVE ADVICE:
   - If you see a suboptimal configuration, mention it
   - Suggest improvements (e.g., "Your medical fund starts late — consider funding from age 50 to reduce the lump sum needed")
   - Warn about risks (e.g., "A growth portfolio for a 5-year horizon is risky")

═══════════════════════════════════════════
REASONING PROCESS (Think step by step):
═══════════════════════════════════════════
Before making changes, ALWAYS:
1. Identify what the user is asking for
2. Check the current values in the scenario JSON
3. Determine the minimal set of changes needed
4. Consider side effects (e.g., changing fund age affects capital required)
5. Explain what you're doing and why in your reply

═══════════════════════════════════════════
OUTPUT FORMAT (STRICT):
═══════════════════════════════════════════
Return ONLY a JSON array of actions. No markdown, no code fences, just raw JSON.

Available actions:
[
  {{"action": "reply", "text": "Your explanation here..."}},
  {{"action": "update_assumption", "key": "inflation|income_return|growth_return|tax_rate|fee_load|tax_free_age", "value": 5.0}},
  {{"action": "update_income", "stage_matches": "Stage 1", "field": "income|start|end|funding_start", "value": 90000}},
  {{"action": "update_car", "name_matches": "Car", "field": "cost|start|cycle|holding|tradein|funding_start|apply_inflation", "value": 60000}},
  {{"action": "update_item", "category": "incomes|cars|assets|travel", "name_matches": "Stage 1", "field": "tax_rate|income_return|growth_return|fee_load|portfolio|start|end|income|cost|cycle|holding|resale|tradein|funding_start|apply_inflation", "value": 0}},
  {{"action": "update_item_portfolio", "category": "incomes|cars|assets|travel", "name_matches": "Stage 1", "portfolio": "conservative|balanced|growth"}},
  {{"action": "update_universal_fund_age", "value": 55}},
  {{"action": "add_child", "name": "Emily", "dob": "2010-05-15"}},
  {{"action": "update_medical", "field": "cost|start|end|funding_start|portfolio", "value": 10000}}
]

═══════════════════════════════════════════
CRITICAL RULES:
═══════════════════════════════════════════
- ALWAYS include a "reply" action explaining what you did and why
- You can combine multiple actions in one response  
- Portfolio options: "conservative" (4.5% income, 0.5% growth), "balanced" (3.5% income, 4.5% growth), "growth" (2.5% income, 6.5% growth)
- tax_free_age: age after which tax on income returns drops to 0%
- universal_fund_age: overrides ALL individual fund-from ages
- Per-item overrides (tax_rate, income_return, growth_return, fee_load) are in PERCENTAGE points (e.g., 15 not 0.15)
- name_matches is case-insensitive partial match (e.g., "stage 1" matches "Stage 1")
- If user asks a question without requesting changes, return ONLY a reply action with a thorough answer
- Reference specific numbers from the scenario when answering questions
- Be concise but thorough in your explanations
"""

    # Build message history for the LLM
    messages = [SystemMessage(content=system_prompt)]
    
    # Add conversation history (keeps context across turns)
    for msg in req.chat_history:
        if msg.role == "user":
            messages.append(HumanMessage(content=msg.content))
        else:
            messages.append(AIMessage(content=msg.content))
    
    # Add the current user message
    messages.append(HumanMessage(content=req.message))
    
    llm = ChatOpenAI(model="gpt-5.2-2025-12-11", temperature=0.1, api_key=api_key)
    resp = llm.invoke(messages)
    
    raw_response = resp.content
    
    try:
        content = raw_response.replace("```json", "").replace("```", "").strip()
        actions = json.loads(content)
        
        reply_text = "Changes applied."
        
        if isinstance(actions, dict): actions = [actions]
        
        for act in actions:
            action_type = act.get("action")
            
            if action_type == "reply":
                reply_text = act.get("text")
                
            elif action_type == "update_assumption":
                key = act.get("key")
                val = act.get("value")
                if hasattr(current_scenario.assumptions, key):
                     setattr(current_scenario.assumptions, key, val)
                     reply_text = f"Updated assumption {key} to {val}"

            elif action_type == "update_income":
                match = act.get("stage_matches", "").lower()
                field = act.get("field")
                value = act.get("value")
                for item in current_scenario.incomes:
                    if match in item.name.lower():
                        setattr(item, field, value)
                        reply_text = f"Updated {item.name}: set {field} to {value}"

            elif action_type == "update_car":
                match = act.get("name_matches", "").lower()
                field = act.get("field")
                value = act.get("value")
                for item in current_scenario.cars:
                    if match in item.name.lower() or match in "car":
                         setattr(item, field, value)
                         reply_text = f"Updated Car: set {field} to {value}"

            elif action_type == "update_item":
                category = act.get("category", "").lower()
                match = act.get("name_matches", "").lower()
                field = act.get("field")
                value = act.get("value")
                
                category_map = {
                    "incomes": current_scenario.incomes,
                    "cars": current_scenario.cars,
                    "assets": current_scenario.assets,
                    "travel": current_scenario.travel,
                }
                items = category_map.get(category, [])
                for item in items:
                    if match in item.name.lower():
                        setattr(item, field, value)
                        reply_text = f"Updated {item.name} ({category}): set {field} to {value}"

            elif action_type == "update_item_portfolio":
                category = act.get("category", "").lower()
                match = act.get("name_matches", "").lower()
                portfolio = act.get("portfolio")
                
                category_map = {
                    "incomes": current_scenario.incomes,
                    "cars": current_scenario.cars,
                    "assets": current_scenario.assets,
                    "travel": current_scenario.travel,
                }
                items = category_map.get(category, [])
                for item in items:
                    if match in item.name.lower():
                        item.portfolio = portfolio
                        reply_text = f"Set {item.name} portfolio to {portfolio}"

            elif action_type == "update_universal_fund_age":
                value = act.get("value")
                current_scenario.universal_fund_age = value
                reply_text = f"Set universal fund age to {value}"

            elif action_type == "add_child":
                name = act.get("name", "Child")
                dob = act.get("dob", "2010-01-01")
                current_scenario.profile.children.append({"name": name, "dob": dob})
                reply_text = f"Added child: {name} (DOB: {dob})"

            elif action_type == "update_medical":
                field = act.get("field")
                value = act.get("value")
                current_scenario.medical[field] = value
                reply_text = f"Updated medical: set {field} to {value}"

    except Exception as e:
        print(f"Agent Error: {e}")
        print(f"Raw LLM response: {raw_response}")
        return {"reply": f"Sorry, I couldn't process that. Error: {e}", "new_results": None, "raw_response": raw_response}

    # Re-Calculate
    new_results, new_total = process_scenario(current_scenario)
    
    return {
        "reply": reply_text,
        "new_scenario": current_scenario.model_dump(),
        "new_results": new_results,
        "new_total": new_total,
        "raw_response": raw_response  # For debugging
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

