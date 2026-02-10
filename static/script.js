document.addEventListener('DOMContentLoaded', () => {
    setupDynamicLists();
    setupAccordion();
    document.getElementById('analysisForm').addEventListener('submit', handleFormSubmit);

    // Add default cars if empty
    if (document.getElementById('carList').children.length === 0) {
        addCarRow('Family Car', 50000, 60, 5, 85);
        addCarRow('Secondary Car', 30000, 60, 10, 80);
    }

    // Add default Stages if empty
    if (document.getElementById('stageList').children.length === 0) {
        addStageRow('Early Active', 60, 75, 100000);
        addStageRow('Late Active', 75, 85, 80000);
        addStageRow('Passive/Frail', 85, 100, 60000);
    }

    // Add default Barriers
    if (document.getElementById('barrierList') && document.getElementById('barrierList').children.length === 0) {
        addBarrierRow('Time', 80);
        addBarrierRow('Fear of Running Out', 60);
        addBarrierRow('Lack of Knowledge', 40);
    }

    // Add default Legacy items if empty (to show examples)
    if (document.getElementById('weddingList').children.length === 0) {
        addLegacyRow('weddingList', 'Daughter Wedding', { pv: 40000, pt: 62 });
    }

    if (document.getElementById('educationList').children.length === 0) {
        addLegacyRow('educationList', 'Grandkids School Fund', { pv: 20000, pt: 65, hc: 20000, dt: 70 });
    }
});

function setupAccordion() {
    const acc = document.getElementsByClassName("accordion");
    for (let i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function () {
            this.classList.toggle("active");
            const panel = this.nextElementSibling;
            if (panel.style.maxHeight) {
                panel.style.maxHeight = null;
            } else {
                panel.style.maxHeight = panel.scrollHeight + "px";
            }
        });
    }
}

function setupDynamicLists() {
    document.getElementById('addCarBtn').addEventListener('click', () => addCarRow());
    document.getElementById('addStageBtn').addEventListener('click', () => addStageRow());
    document.getElementById('addBarrierBtn').addEventListener('click', () => addBarrierRow());
    document.getElementById('addWeddingBtn').addEventListener('click', () => addLegacyRow('weddingList', 'Wedding'));
    document.getElementById('addDepositBtn').addEventListener('click', () => addLegacyRow('depositList', 'Home Deposit'));
    document.getElementById('addEducationBtn').addEventListener('click', () => addLegacyRow('educationList', 'School Fees'));
}

// Helper to create the Vehicle Input Group (With Cycle)
function createVehicleRow(namePlaceholder, defaultVals = {}) {
    const div = document.createElement('div');
    div.className = 'dynamic-item five-attr-grid';

    const vals = {
        name: defaultVals.name || '',
        pv: defaultVals.pv || '',
        pt: defaultVals.pt || 60,
        cycle: defaultVals.cycle || 5, // Default 5yr cycle
        dt: defaultVals.dt || 80
    };

    div.innerHTML = `
        <div class="form-group">
            <label>Name</label>
            <input type="text" class="item-name" placeholder="${namePlaceholder}" value="${vals.name}" required>
        </div>
        <div class="form-group">
            <label>Cost ($)</label>
            <input type="number" class="item-pv" placeholder="Price" value="${vals.pv}" required>
        </div>
        <div class="form-group">
            <label>Start Age</label>
            <input type="number" class="item-pt" placeholder="e.g. 60" value="${vals.pt}" required>
        </div>
        <div class="form-group">
            <label>Hold Cost ($/yr)</label>
            <input type="number" class="item-hc" placeholder="Rego/Ins" value="${vals.hc || 1500}">
        </div>
        <div class="form-group">
            <label>Cycle (Yrs)</label>
            <input type="number" class="item-cycle" placeholder="Change every..." value="${vals.cycle}">
        </div>
        <div class="form-group">
            <label>End Age</label>
            <input type="number" class="item-dt" placeholder="Stop driving" value="${vals.dt}" required>
        </div>
        <button type="button" class="remove-btn" onclick="this.parentElement.remove()">×</button>
    `;
    return div;
}

function addCarRow(name, pv, pt, cycle, dt) {
    const row = createVehicleRow('Car Description', { name, pv, pt, cycle, dt });
    document.getElementById('carList').appendChild(row);
}

// Helper for Generic 5-Attribute Items (Legacy, Education, etc.)
function create5AttrRow(namePlaceholder, defaultVals = {}) {
    const div = document.createElement('div');
    div.className = 'dynamic-item five-attr-grid';

    const vals = {
        name: defaultVals.name || '',
        pv: defaultVals.pv || '',
        pt: defaultVals.pt || 0,
        hc: defaultVals.hc || 0,
        dt: defaultVals.dt || 0,
        dv: defaultVals.dv || 0
    };

    div.innerHTML = `
        <div class="form-group">
            <label>Item Name</label>
            <input type="text" class="item-name" placeholder="${namePlaceholder}" value="${vals.name}" required>
        </div>
        <div class="form-group">
            <label>Value/Cost ($)</label>
            <input type="number" class="item-pv" placeholder="Purch. Value" value="${vals.pv}" required>
        </div>
        <div class="form-group">
            <label>Start (Age)</label>
            <input type="number" class="item-pt" placeholder="Timing" value="${vals.pt}" required>
        </div>
        <div class="form-group">
            <label>Hold Cost ($/yr)</label>
            <input type="number" class="item-hc" placeholder="Annual" value="${vals.hc}">
        </div>
        <div class="form-group">
            <label>End (Age)</label>
            <input type="number" class="item-dt" placeholder="Disposal" value="${vals.dt}" required>
        </div>
        <div class="form-group">
            <label>End Value ($)</label>
            <input type="number" class="item-dv" placeholder="Resid. Val" value="${vals.dv}">
        </div>
        <button type="button" class="remove-btn" onclick="this.parentElement.remove()">×</button>
    `;
    return div;
}

function addLegacyRow(listId, namePrefix, defaultVals = {}) {
    // Merge defaults. If user passes just {pv: 50000}, we want namePrefix to still be the name if not overridden?
    // create5AttrRow uses defaultVals.name.
    // Let's overwrite name if not provided in defaultVals.
    if (!defaultVals.name) defaultVals.name = `${namePrefix} Description`;

    const row = create5AttrRow(namePrefix, defaultVals);
    document.getElementById(listId).appendChild(row);
}

function get5AttrItems(listId) {
    const list = document.getElementById(listId);
    const items = [];
    if (list) {
        list.querySelectorAll('.dynamic-item').forEach(row => {
            items.push({
                name: row.querySelector('.item-name').value,
                purchase_value: parseFloat(row.querySelector('.item-pv').value) || 0,
                purchase_timing: parseInt(row.querySelector('.item-pt').value) || 0,
                holding_cost: parseFloat(row.querySelector('.item-hc').value) || 0,
                disposal_timing: parseInt(row.querySelector('.item-dt').value) || 100,
                disposal_value: parseFloat(row.querySelector('.item-dv').value) || 0
            });
        });
    }
    return items;
}

function getItemFromInputs(prefix) {
    return {
        name: prefix,
        purchase_value: parseFloat(document.getElementById(prefix + '_budget').value) || 0,
        purchase_timing: parseInt(document.getElementById(prefix + '_start').value) || 60,
        holding_cost: 0,
        disposal_timing: parseInt(document.getElementById(prefix + '_end').value) || 90,
        disposal_value: 0
    };
}

function createStageRow(name, start, end, income) {
    const div = document.createElement('div');
    div.className = 'dynamic-item five-attr-grid'; // Use same grid layout
    div.style.gridTemplateColumns = '2fr 1fr 1fr 1fr 0.5fr'; // Custom columns if needed, but flex works

    div.innerHTML = `
        <div class="form-group">
            <label>Stage Name</label>
            <input type="text" class="item-name" placeholder="e.g. Early Active" value="${name || ''}" required>
        </div>
        <div class="form-group">
            <label>Start Age</label>
            <input type="number" class="item-start" placeholder="60" value="${start || 60}" required>
        </div>
        <div class="form-group">
            <label>End Age</label>
            <input type="number" class="item-end" placeholder="75" value="${end || 75}" required>
        </div>
        <div class="form-group">
            <label>Income Needed ($/yr)</label>
            <input type="number" class="item-income" placeholder="100000" value="${income || 80000}" required>
        </div>
        <button type="button" class="remove-btn" onclick="this.parentElement.remove()">×</button>
    `;
    return div;
}

function addStageRow(name, start, end, income) {
    const row = createStageRow(name, start, end, income);
    document.getElementById('stageList').appendChild(row);
}

function getStageItems() {
    const list = document.getElementById('stageList');
    const items = [];
    if (list) {
        list.querySelectorAll('.dynamic-item').forEach(row => {
            items.push({
                name: row.querySelector('.item-name').value,
                start_age: parseInt(row.querySelector('.item-start').value) || 60,
                end_age: parseInt(row.querySelector('.item-end').value) || 85,
                annual_income: parseFloat(row.querySelector('.item-income').value) || 50000
            });
        });
    }
    return items;
}

function createBarrierRow(desc, pct) {
    const div = document.createElement('div');
    div.className = 'dynamic-item five-attr-grid';
    div.style.gridTemplateColumns = '3fr 1fr 0.5fr'; // Description, %, remove

    div.innerHTML = `
        <div class="form-group">
            <label>Barrier Description</label>
            <input type="text" class="item-desc" placeholder="e.g. Fear of conflict" value="${desc || ''}" required>
        </div>
        <div class="form-group">
            <label>Impact %</label>
            <input type="number" class="item-pct" placeholder="0-100" value="${pct || 50}" required>
        </div>
        <button type="button" class="remove-btn" onclick="this.parentElement.remove()">×</button>
    `;
    return div;
}

function addBarrierRow(desc, pct) {
    const row = createBarrierRow(desc, pct);
    document.getElementById('barrierList').appendChild(row);
}

function getBarrierItems() {
    const list = document.getElementById('barrierList');
    const items = [];
    if (list) {
        list.querySelectorAll('.dynamic-item').forEach(row => {
            items.push({
                description: row.querySelector('.item-desc').value,
                impact_percentage: parseInt(row.querySelector('.item-pct').value) || 0
            });
        });
    }
    return items;
}

function getVehicleItems(listId) {
    const list = document.getElementById(listId);
    const items = [];
    if (list) {
        list.querySelectorAll('.dynamic-item').forEach(row => {
            items.push({
                name: row.querySelector('.item-name').value,
                purchase_value: parseFloat(row.querySelector('.item-pv').value) || 0,
                start_age: parseInt(row.querySelector('.item-pt').value) || 0,
                replacement_cycle: parseInt(row.querySelector('.item-cycle').value) || 10,
                holding_cost: parseFloat(row.querySelector('.item-hc').value) || 0,
                end_age: parseInt(row.querySelector('.item-dt').value) || 90
            });
        });
    }
    return items;
}

async function handleFormSubmit(e) {
    e.preventDefault();
    let btn = e.submitter;
    if (!btn) btn = e.target.querySelector('button[type="submit"]');

    let originalText = 'Generate Life Strategy ➞'; // Default fallback
    if (btn) {
        originalText = btn.innerText;
        btn.innerText = 'Consulting Life Strategist (approx 30s)...';
        btn.disabled = true;
    }

    try {
        const formData = {
            profile: {
                partner1_name: document.getElementById('p1_name').value,
                partner1_dob: document.getElementById('p1_dob').value,
                partner2_name: document.getElementById('p2_name').value || null,
                partner2_dob: document.getElementById('p2_dob').value || null,
                partner1_retirement_age: parseInt(document.getElementById('p1_retire_age').value) || 65,
                partner2_retirement_age: parseInt(document.getElementById('p2_retire_age').value) || 60,

                // Split text areas by comma
                wants: document.getElementById('wants_list').value.split(',').map(s => s.trim()).filter(s => s),
                dont_wants: document.getElementById('dont_wants_list').value.split(',').map(s => s.trim()).filter(s => s),
                barriers: getBarrierItems(),

                eulogy_partner: document.getElementById('eulogy_partner').value,
                eulogy_child: document.getElementById('eulogy_child').value,
                eulogy_friend: document.getElementById('eulogy_friend').value
            },
            context: {
                super_balance: parseFloat(document.getElementById('asset_super').value) || 0,
                cash_savings: parseFloat(document.getElementById('asset_cash').value) || 0,
                shares_investments: parseFloat(document.getElementById('asset_shares').value) || 0,
                investment_properties: parseFloat(document.getElementById('asset_props').value) || 0,
                other_assets: 0
            },
            big_rocks: {
                primary_residence: {
                    current_value: parseFloat(document.getElementById('home_val').value) || 0,
                    outstanding_mortgage: parseFloat(document.getElementById('home_debt').value) || 0,
                    holding_cost: parseFloat(document.getElementById('home_cost').value) || 0,
                    strategy: document.getElementById('home_strat').value,
                    dwelling_type: document.getElementById('home_type').value,
                    location_type: document.getElementById('home_loc').value,
                    growth_assumption: document.getElementById('home_growth').value
                },
                // ... (Holiday home logic remains similar)
                holiday_home: {
                    name: 'Holiday Home',
                    purchase_value: parseFloat(document.getElementById('hol_val').value) || 0,
                    purchase_timing: 0,
                    holding_cost: parseFloat(document.getElementById('hol_cost').value) || 0,
                    disposal_timing: 80,
                    disposal_value: 0
                },
                aged_care: {
                    entry_age: parseInt(document.getElementById('ac_entry').value) || 85,
                    rad_deposit: parseFloat(document.getElementById('ac_rad').value) || 1000000,
                    daily_fees: 0
                }
            },
            lifestyle: {
                cars: getVehicleItems('carList'),

                // Granular Travel
                travel_international: {
                    name: "International Travel",
                    duration_days: parseInt(document.getElementById('trv_i_days').value) || 0,
                    flight_cost_per_person: parseFloat(document.getElementById('trv_i_flight').value) || 2500,
                    seasonality: document.getElementById('trv_i_season').value,
                    cost_accom_daily: parseFloat(document.getElementById('trv_i_accom').value) || 0,
                    cost_transport_daily: 0,
                    cost_food_daily: parseFloat(document.getElementById('trv_i_food').value) || 0,
                    cost_fun_daily: parseFloat(document.getElementById('trv_i_fun').value) || 0,
                    start_age: parseInt(document.getElementById('trv_i_start').value) || 60,
                    end_age: parseInt(document.getElementById('trv_i_end').value) || 80
                },
                travel_domestic: {
                    name: "Domestic Travel",
                    duration_days: parseInt(document.getElementById('trv_d_days').value) || 0,
                    cost_accom_daily: parseFloat(document.getElementById('trv_d_daily').value) || 0,
                    cost_transport_daily: 0, cost_food_daily: 0, cost_fun_daily: 0,
                    start_age: parseInt(document.getElementById('trv_d_start').value) || 60,
                    end_age: parseInt(document.getElementById('trv_d_end').value) || 85
                },
                travel_parents: {
                    name: "Travel to Parents",
                    duration_days: 7,
                    cost_accom_daily: parseFloat(document.getElementById('trv_parents').value) || 0,
                    cost_transport_daily: 0, cost_food_daily: 0, cost_fun_daily: 0,
                    start_age: 60, end_age: 80, flight_cost_per_person: 0
                },
                travel_others: {
                    name: "Other Travel",
                    duration_days: 7,
                    cost_accom_daily: parseFloat(document.getElementById('trv_others').value) || 0,
                    cost_transport_daily: 0, cost_food_daily: 0, cost_fun_daily: 0,
                    start_age: 60, end_age: 80, flight_cost_per_person: 0
                },

                // Specific Assets
                boat: {
                    name: "Boat",
                    purchase_value: parseFloat(document.getElementById('asset_boat').value) || 0,
                    purchase_timing: 60, holding_cost: 5000, disposal_timing: 70, disposal_value: 0
                },
                caravan: {
                    name: "Caravan",
                    purchase_value: parseFloat(document.getElementById('asset_caravan').value) || 0,
                    purchase_timing: 60, holding_cost: 2000, disposal_timing: 75, disposal_value: 0
                },

                // Life Stages (The Big Change)
                life_stages: getStageItems(),

                // Medical
                medical_expenses: {
                    name: "Medical Expenses",
                    purchase_value: parseFloat(document.getElementById('med_cost').value) || 0,
                    purchase_timing: 60, holding_cost: 0, disposal_timing: 100, disposal_value: 0
                },

                health_buffer: {
                    name: 'Health Buffer',
                    purchase_value: parseFloat(document.getElementById('health_cost').value) || 5000,
                    purchase_timing: 60, holding_cost: 0, disposal_timing: 100, disposal_value: 0
                },
                emergency_reserve: parseFloat(document.getElementById('emergency_res').value) || 50000
            },
            family: {
                wedding_contributions: get5AttrItems('weddingList'),
                home_deposits: get5AttrItems('depositList'),
                education_support: get5AttrItems('educationList')
            },
            assumptions: {
                general_inflation: parseFloat(document.getElementById('asm_inf_gen').value),
                education_inflation: parseFloat(document.getElementById('asm_inf_edu').value),
                car_depreciation: parseFloat(document.getElementById('asm_dep_car').value),
                fee_load: parseFloat(document.getElementById('asm_fees').value),
                risk_profile: document.getElementById('asm_risk').value
            }
        };

        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (response.ok) {
            const result = await response.json();
            // Store result in local storage or pass via URL? 
            // Better to render result.html directly from backend response?
            // The plan said "POST /analyze (Form submission handler): Renders result.html".
            // If I am using fetch, I need to handle the HTML response manually.
            // Let's assume /api/analyze returns JSON and we render it on client OR we use a FORM POST.
            // My Script is doing fetch. I'll switch to a FORM POST if I want simple rendering, 
            // BUT, strictly speaking, a Single Page App "Proto" feel is better.
            // However, the user wants "Result Rendering templates/result.html".
            // I will replace the document body with the HTML returned if I modify the backend to return HTML,
            // OR I will simply display the JSON if the backend returns JSON.
            // The Plan said: "POST /analyze (Form submission handler): Renders result.html with data."
            // So my `main.py` will have a Form handler.
            // BUT, `main.py` plan also says: "POST /api/analyze: ... Returns structured JSON."
            // I will support BOTH or just use the JSON API for the "Logic" and have a separate rendering route.
            // To make it simple for the user instructions:
            // I will simply `document.write(html)` if I return HTML, or redirect.

            // Re-reading logic: Prototype. 
            // Simplest: Send JSON -> Receive JSON -> Render JSON into a nice view (Client Side Rendering) 
            // OR Send JSON -> API returns rendered HTML string? No, API usually returns JSON.

            // I will make the valid approach:
            // Client sends JSON. Client receives JSON. Client renders "Result View" by hiding form and showing result div.
            // This is cleaner for a "clean HTML page" constraint.
            // Wait, constraint: "Frontend: A single, clean HTML page using Jinja2 templates".
            // This implies server-side rendering is expected for the RESULT page optionally.

            // Let's stick to: FETCH -> receive JSON -> Populate a 'Results' modal/overlay or redirect to a results page with the data?
            // I'll make the fetch response trigger a page rewrite or local display. Use localStorage to pass data to a results.html?
            // Cleanest: Backend returns JSON. JS populates a hidden #results section in index.html.
            // This keeps it a "Single Page".

            renderResults(result); // I will implement this function to populate the view.
        } else {
            alert('Error calculating plan. Please check inputs.');
        }

    } catch (err) {
        console.error(err);
        alert('System Error: ' + err.message);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

function renderResults(data) {
    // Hide form, show results
    document.getElementById('inputSection').style.display = 'none';
    const resDiv = document.getElementById('resultSection');
    resDiv.style.display = 'block';

    // 1. Narrative & True North
    document.getElementById('res_narrative').innerHTML = `
        <p>"${data.client_narrative}"</p>
        <div style="margin-top:20px; font-style:normal; font-size:0.9rem;">
            <strong>Top 3 Wants:</strong> ${data.true_north.top_3_wants.join(', ')}<br>
            <strong>Top 3 Avoids:</strong> ${data.true_north.top_3_dont_wants.join(', ')}
        </div>
    `;

    // 2. Two Numbers
    document.getElementById('res_num1').innerText = '$' + data.two_numbers.necessary_life_capital.toLocaleString();
    document.getElementById('res_num2').innerText = '$' + data.two_numbers.best_life_capital.toLocaleString();
    document.getElementById('res_gap').innerText = data.two_numbers.gap_analysis;

    // 3. Capital Architecture (Buckets)
    const bucketsDiv = document.getElementById('res_buckets');
    if (bucketsDiv && data.capital_structure) {
        const b1 = data.capital_structure.bucket_1;
        const b2 = data.capital_structure.bucket_2;
        const b3 = data.capital_structure.bucket_3;

        bucketsDiv.innerHTML = `
            <div class="bucket-card">
                <h4>Bucket 1: Stability</h4>
                <div class="bucket-val">$${b1.target_amount.toLocaleString()}</div>
                <p style="font-size:0.8rem; color:var(--text-secondary);">Funded: $${b1.funded_amount.toLocaleString()}</p>
                <p style="color:var(--danger-color);">Gap: $${b1.gap.toLocaleString()}</p>
            </div>
            <div class="bucket-card">
                <h4>Bucket 2: Momentum</h4>
                <div class="bucket-val">$${b2.target_amount.toLocaleString()}</div>
                 <p style="font-size:0.8rem; color:var(--text-secondary);">Funded: $${b2.funded_amount.toLocaleString()}</p>
                <p style="color:var(--danger-color);">Gap: $${b2.gap.toLocaleString()}</p>
            </div>
            <div class="bucket-card">
                <h4>Bucket 3: Growth</h4>
                <div class="bucket-val">$${b3.target_amount.toLocaleString()}</div>
                 <p style="font-size:0.8rem; color:var(--text-secondary);">Funded: $${b3.funded_amount.toLocaleString()}</p>
                <p style="color:var(--danger-color);">Gap: $${b3.gap.toLocaleString()}</p>
            </div>
            <div class="full-width" style="margin-top:10px; font-style:italic; opacity:0.8; font-size: 0.9em; text-align: left;">
                ${data.capital_structure.explanation}
            </div>
        `;
    }

    // 4. Lifeline Register Table (NEW)
    // Create container if not exists (it doesn't in HTML, so we inject)
    // 4. Lifeline Register Table (NEW)
    // Create container if not exists (it doesn't in HTML, so we inject)
    let regDiv = document.getElementById('res_register_container');
    if (!regDiv) {
        regDiv = document.createElement('div');
        regDiv.id = 'res_register_container';
        regDiv.className = 'section-card';
        regDiv.style.marginTop = '30px';

        // Find the Assumptions Section Card
        const assumptionsPre = document.getElementById('res_assumptions');
        const assumptionsCard = assumptionsPre ? assumptionsPre.closest('.section-card') : null;

        if (assumptionsCard && assumptionsCard.parentNode === resDiv) {
            resDiv.insertBefore(regDiv, assumptionsCard);
        } else {
            // Fallback: just append it to the main container
            resDiv.appendChild(regDiv);
        }
    }

    let regHtml = `<h3>The Lifeline Register (5-Attribute Rule)</h3>
                   <div style="overflow-x:auto;">
                   <table style="width:100%; border-collapse: collapse; font-size:0.9rem;">
                   <thead style="background:rgba(255,255,255,0.1); border-bottom:1px solid var(--border-color);">
                       <tr>
                           <th style="padding:10px; text-align:left;">Item</th>
                           <th style="padding:10px; text-align:left;">Category</th>
                           <th style="padding:10px; text-align:right;">Purchase Val</th>
                           <th style="padding:10px; text-align:center;">Start</th>
                           <th style="padding:10px; text-align:right;">Hold/Yr</th>
                           <th style="padding:10px; text-align:center;">End</th>
                           <th style="padding:10px; text-align:right;">Disposal</th>
                       </tr>
                   </thead>
                   <tbody>`;

    data.lifeline_register.forEach(item => {
        regHtml += `<tr style="border-bottom:1px solid rgba(255,255,255,0.05);">
                        <td style="padding:10px;">${item.item_name}</td>
                        <td style="padding:10px; color:var(--accent-color);">${item.category}</td>
                        <td style="padding:10px; text-align:right;">$${item.purchase_value.toLocaleString()}</td>
                        <td style="padding:10px; text-align:center;">${item.purchase_timing}</td>
                        <td style="padding:10px; text-align:right;">$${item.holding_cost.toLocaleString()}</td>
                        <td style="padding:10px; text-align:center;">${item.disposal_timing}</td>
                        <td style="padding:10px; text-align:right;">$${item.disposal_value.toLocaleString()}</td>
                    </tr>`;
    });
    regHtml += `</tbody></table></div>`;
    regDiv.innerHTML = regHtml;

    // 5. Resilience
    const riskDiv = document.getElementById('res_resilience');
    if (riskDiv && data.resilience_report) {
        riskDiv.innerHTML = `
            <div style="margin-bottom: 8px;"><strong style="color:var(--highlight-color);">📉 Market Shock (30% Drop):</strong> ${data.resilience_report.market_shock_response}</div>
            <div style="margin-bottom: 8px;"><strong style="color:var(--highlight-color);">🏥 Health Crisis:</strong> ${data.resilience_report.health_event_response}</div>
            <div style="margin-bottom: 8px;"><strong style="color:var(--highlight-color);">🕊 Early Departure:</strong> ${data.resilience_report.early_death_implication}</div>
            <div style="margin-bottom: 8px;"><strong style="color:var(--highlight-color);">🕰 Longevity (100+):</strong> ${data.resilience_report.longevity_check}</div>
         `;
    }

    // 6. Fees
    document.getElementById('res_fees').innerText = '$' + data.fee_relativity.total_estimated_fees_10y.toLocaleString();
    document.getElementById('res_lifefunded').innerText = '$' + data.fee_relativity.total_life_funded_value.toLocaleString();
    document.getElementById('res_fee_narrative').innerText = data.fee_relativity.fee_ratio_narrative;

    // 7. Assumptions
    document.getElementById('res_assumptions').innerText = JSON.stringify(data.assumptions_log, null, 2);

    window.scrollTo(0, 0);
}
async function downloadPDF() {
    const btn = document.getElementById('downloadPdfBtn');
    const originalText = btn.innerText;
    btn.innerText = 'Generating PDF...';
    btn.disabled = true;

    try {
        const element = document.getElementById('resultSection');

        // Clone to clean up for PDF (remove button)
        const clone = element.cloneNode(true);
        const btnInClone = clone.querySelector('#downloadPdfBtn');
        if (btnInClone) btnInClone.remove();

        // TRANSFORM INPUTS TO TEXT
        // Inputs cannot wrap text, which causes overflow in tables. 
        // We replace them with their values in spans/divs.
        const inputs = clone.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            const span = document.createElement('span');
            span.style.wordWrap = 'break-word';
            span.style.whiteSpace = 'pre-wrap';

            if (input.tagName === 'SELECT') {
                // Get selected text, not value
                span.innerText = input.options[input.selectedIndex]?.text || input.value;
            } else {
                span.innerText = input.value;
            }
            input.parentNode.replaceChild(span, input);
        });


        // Create dedicated Print CSS for WeasyPrint
        const cssContent = `
            @page {
                size: A4;
                margin: 25mm 20mm;
                @top-center {
                    content: "Beresfords Life-First Strategy";
                    font-family: serif;
                    font-size: 9pt;
                    color: #666;
                }
                @bottom-center {
                    content: counter(page);
                    font-family: serif;
                    font-size: 9pt;
                    color: #666;
                }
            }
            body { 
                font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; 
                line-height: 1.5; 
                color: #333; 
                background: #fff;
                font-size: 11pt;
            }
            h2 { 
                color: #1a365d; 
                border-bottom: 2px solid #1a365d; 
                padding-bottom: 5px; 
                margin-top: 30px; 
                margin-bottom: 15px; 
                font-size: 18pt;
                page-break-after: avoid;
            }
            h3 { 
                color: #2c5282; 
                font-size: 14pt; 
                margin-top: 20px; 
                margin-bottom: 10px; 
                page-break-after: avoid;
            }
            .section-card { 
                border: 1px solid #e2e8f0; 
                border-radius: 8px; 
                padding: 20px; 
                margin-bottom: 25px; 
                background: #fff;
                page-break-inside: avoid;
            }
            .form-grid {
                display: block; /* WeasyPrint handles flows better than complex grids sometimes, but let's try strict flex */
                overflow: hidden;
            }
            /* Emulate grid with float/width for reliability in PDF engines if grid fails, 
               but WeasyPrint supports flex/grid reasonably well now. Let's use clean block layout for safety or Flex */
            .form-grid > div {
                margin-bottom: 15px;
            }
            
            /* Two-Column Layout for Key Numbers */
            #res_num1, #res_num2 {
                font-size: 24pt !important;
                font-weight: bold;
                margin: 10px 0;
            }
            #res_num1 { color: #2f855a !important; } /* Green */
            #res_num2 { color: #c53030 !important; } /* Red/Accent */

            .highlight-box {
                background-color: #f7fafc;
                border: 1px solid #cbd5e0;
                padding: 15px;
                border-radius: 5px;
            }
            
            /* Table-like structures */
            .five-attr-grid {
                display: table;
                width: 100%;
                table-layout: fixed; /* Force equal width or respect percentages */
                border-collapse: collapse;
                margin-bottom: 10px;
                font-size: 8pt; /* Reduce base font for table */
            }
            .five-attr-grid .form-group {
                display: table-cell;
                padding: 4px;
                border: 1px solid #eee;
                word-wrap: break-word; /* Prevent overflow */
                vertical-align: top;
            }
            label {
                display: block;
                font-weight: bold;
                font-size: 7pt;
                color: #666;
                text-transform: uppercase;
                margin-bottom: 2px;
            }
            .value-display {
                font-size: 9pt;
            }
            
            /* Assumptions Log - Fix Overflow */
            #res_assumptions {
                white-space: pre-wrap;       /* Wrap text */
                word-wrap: break-word;       /* Break long words */
                font-family: "Courier New", Courier, monospace;
                font-size: 8pt;
                background: #f4f4f4;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                max-width: 100%;
            }
        `;

        const htmlContent = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
            </head>
            <body>
                <div class="results-container">
                    ${clone.innerHTML}
                </div>
            </body>
            </html>
        `;

        const response = await fetch('/api/pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ html_content: htmlContent, css_content: cssContent })
        });

        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'Beresfords_Life_Strategy.pdf';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } else {
            alert('Server failed to generate PDF. Check inputs.');
        }

    } catch (err) {
        console.error(err);
        alert('Error: ' + err.message);
    } finally {
        btn.innerText = originalText;
        btn.disabled = false;
    }
}
