from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date

# --- 1. Assumptions & Settings (Dynamic) ---
# --- 1. Assumptions & Settings (Dynamic) ---
class Assumptions(BaseModel):
    general_inflation: float = Field(3.3, description="General inflation rate %")
    education_inflation: float = Field(8.0, description="Education specific inflation rate %")
    car_depreciation: float = Field(15.0, description="Car depreciation rate %")
    fee_load: float = Field(1.5, description="Estimated total fee load %")
    risk_profile: str = Field("Balanced", description="Conservative, Moderate, Balanced, Growth, Pure Growth")

# --- 2. Client Profile & True North ---
class ClientProfile(BaseModel):
    partner1_name: str
    partner1_dob: date
    partner2_name: Optional[str] = None
    partner2_dob: Optional[date] = None
    partner1_retirement_age: int = Field(65, description="P1 Planned retirement age")
    partner2_retirement_age: int = Field(60, description="P2 Planned retirement age")
    
    # True North (The Why)
    # Doctrine: Top 10 Rules + Barriers + 3 Eulogies
    wants: List[str] = Field(..., description="Top 10 Wants")
    dont_wants: List[str] = Field(..., description="Top 10 Don't Wants")
    
    class Barrier(BaseModel):
        description: str
        impact_percentage: int = Field(..., description="0-100% impact")
        
    barriers: List[Barrier] = Field(..., description="What prevented these?")
    
    eulogy_partner: str
    eulogy_child: str
    eulogy_friend: str

# --- 3. The 5-Attribute Rule Base ---
class LifestyleItem(BaseModel):
    name: str
    purchase_value: float
    purchase_timing: int
    holding_cost: float
    disposal_timing: int
    disposal_value: float

class VehicleItem(BaseModel):
    name: str
    purchase_value: float
    start_age: int
    replacement_cycle: int = Field(..., description="Replace every X years")
    holding_cost: float = Field(..., description="Annual Rego/Ins/Maint")
    end_age: int

class TravelDetailed(BaseModel):
    name: str = "Annual Travel"
    duration_days: int
    flight_cost_per_person: float = Field(0.0, description="flights are per trip, not per day")
    seasonality: str = Field("Shoulder", description="Peak, Shoulder, Off-Peak")
    cost_accom_daily: float
    cost_food_daily: float
    cost_fun_daily: float
    start_age: int
    end_age: int
    
    @property
    def total_annual_cost(self) -> float:
        # Assuming 2 people for flights if not specified, but logic is handled in Main Prompt usually.
        # Ideally we know num_pax. For now, prompt handles logic.
        daily_sum = self.cost_accom_daily + self.cost_food_daily + self.cost_fun_daily
        return (self.duration_days * daily_sum) + (self.flight_cost_per_person * 2) # Assume couple

# --- 4. The Big Rocks ---
class Residence(BaseModel):
    current_value: float
    outstanding_mortgage: float
    holding_cost: float = Field(..., description="Rates, Insurance, Maint/yr")
    strategy: str
    # Growth Tags
    dwelling_type: str = Field(..., description="House vs Unit")
    location_type: str = Field(..., description="City vs Rural")
    growth_assumption: str = Field(..., description="Low, Average, High")

class AgedCare(BaseModel):
    entry_age: int = Field(85, description="Default 85")
    rad_deposit: float = Field(1000000, description="Refundable Accommodation Deposit")
    daily_fees: float = Field(0.0, description="Means-tested fees")

class BigRocks(BaseModel):
    primary_residence: Residence
    holiday_home: Optional[LifestyleItem] = None
    aged_care: AgedCare

# --- 5. Lifestyle Layers ---
class FamilyLegacy(BaseModel):
    wedding_contributions: List[LifestyleItem] = [] 
    home_deposits: List[LifestyleItem] = []
    education_support: List[LifestyleItem] = [] 

class LifeStage(BaseModel):
    name: str = Field(..., description="e.g. Early, Family, Late")
    start_age: int
    end_age: int
    annual_income: float = Field(..., description="Net income needed per year in this stage") 

class Lifestyle(BaseModel):
    cars: List[VehicleItem]
    
    # Granular Travel
    travel_domestic: Optional[TravelDetailed] = None
    travel_international: Optional[TravelDetailed] = None
    travel_parents: Optional[TravelDetailed] = None
    travel_others: Optional[TravelDetailed] = None

    # Specific Luxury Assets
    boat: Optional[LifestyleItem] = None
    caravan: Optional[LifestyleItem] = None
    
    # Life Stages (Flexible Income)
    life_stages: List[LifeStage]
    
    # Buffers
    health_buffer: LifestyleItem
    medical_expenses: Optional[LifestyleItem] = None # Recurring medical costs
    emergency_reserve: float = Field(..., description="Sleep at night capital (Bucket 1)")

class FinancialContext(BaseModel):
    # Starting Capital (Crucial for Bucket Filling)
    super_balance: float = 0.0
    cash_savings: float = 0.0
    shares_investments: float = 0.0
    investment_properties: float = 0.0
    other_assets: float = 0.0
    
    @property
    def total_investable(self) -> float:
        return self.super_balance + self.cash_savings + self.shares_investments + self.other_assets

# --- Root Input Model ---
class SystemInput(BaseModel):
    profile: ClientProfile
    big_rocks: BigRocks
    lifestyle: Lifestyle
    family: FamilyLegacy
    context: FinancialContext = Field(default_factory=FinancialContext)
    assumptions: Assumptions = Field(default_factory=Assumptions)

# --- Output Structures ---
# --- Output Structures ---

class LifelineItemDetail(BaseModel):
    item_name: str = Field(..., description="e.g. 'Family Car', 'International Travel (Active)'")
    category: str = Field(..., description="Transport, Housing, Lifestyle, Travel, etc.")
    purchase_value: float = Field(..., description="(1) Cost/Value")
    purchase_timing: str = Field(..., description="(2) Start Age/Year")
    holding_cost: float = Field(..., description="(3) Annual Holding Cost")
    disposal_timing: str = Field(..., description="(4) End Age/Year")
    disposal_value: float = Field(..., description="(5) Residual Value")

class CapitalRequirement(BaseModel):
    category: str = Field(..., description="e.g. 'Necessary Life', 'Best Life - Travel'")
    lump_sum_required: float = Field(..., description="Capital needed at retirement to fund this stream")
    details: str = Field(..., description="Brief explaination of calculation")

class BucketDetail(BaseModel):
    bucket_name: str
    purpose: str
    target_amount: float = Field(..., description="The calculated requirement")
    funded_amount: float = Field(..., description="Actual items/cash currently allocating to this")
    gap: float = Field(..., description="Deficit (Target - Funded)")

class BucketStructure(BaseModel):
    bucket_1: BucketDetail
    bucket_2: BucketDetail
    bucket_3: BucketDetail
    explanation: str

class TrueNorthComponents(BaseModel):
    top_3_wants: List[str]
    top_3_dont_wants: List[str]
    true_north_statement: str


class TwoNumbers(BaseModel):
    necessary_life_capital: float = Field(..., description="Cost of dignity, housing, health, basic flows")
    best_life_capital: float = Field(..., description="Necessary + Travel + Luxury + Generosity + True North")
    gap_analysis: str

class ResilienceReport(BaseModel):
    market_shock_response: str = Field(..., description="What happens if markets drop 30%?")
    health_event_response: str = Field(..., description="Impact of early aged care or medical shock")
    early_death_implication: str = Field(..., description="Financial position if life ends early")
    longevity_check: str = Field(..., description="Survival to age 100+")

class FeeRelativity(BaseModel):
    total_estimated_fees_10y: float
    total_life_funded_value: float
    fee_ratio_narrative: str

class KeyValuePair(BaseModel):
    key: str
    value: str

class AssumptionsLog(BaseModel):
    inflation_rates_used: List[KeyValuePair]
    return_rates_used: List[KeyValuePair]
    depreciation_rules_applied: str
    fee_assumptions: str

class SystemOutput(BaseModel):
    true_north: TrueNorthComponents
    client_narrative: str = Field(..., description="Poetic, empathetic summary")
    lifeline_register: List[LifelineItemDetail] = Field(..., description="The FULL 5-Attribute register of every item")
    capital_requirements: List[CapitalRequirement] = Field(..., description="Reverse-engineered capital breakdown")
    two_numbers: TwoNumbers
    capital_structure: BucketStructure
    resilience_report: ResilienceReport
    fee_relativity: FeeRelativity
    assumptions_log: AssumptionsLog
